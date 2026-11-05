"""
MediFlow — Motor de Testes de Carga Concorrente e Stress Clínico (Release 1.4)
Hackathon ONE G10 — Oracle Next Education & Alura (Equipo 22)
Persona Responsável: Arquiteto Carlos Vance (Carlos Magno — Tech Lead & Líder SRE/DevOps)
"""

from __future__ import annotations

import concurrent.futures
import logging
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Adiciona diretório raiz ao path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from mediflow_schemas import DocumentoClinicoInput, TipoArquivoEnum
from week3.agent import (
    MediFlowStateGraphAgent,
    SCENARIO_1_ROUTINE,
    SCENARIO_2_URGENCY_TEP,
    SCENARIO_3_AMBIGUOUS_HITL,
)
from week3.notifications import NotificationDispatcher
from week3.storage import OCIStorageServiceV3

logger = logging.getLogger("mediflow.load_testing")


class ConcurrentLoadTester:
    """
    Gerador e avaliador de carga concorrente para o agente LangGraph.
    Simula picos de admissão hospitalar simultânea e valida:
      1. Ausência de condições de corrida (Race Conditions) e deadlocks.
      2. Vazão sustentada (Throughput em Requests per Second - RPS).
      3. Cumprimento estrito do SLA de latência (< 5000ms) sob estresse.
      4. Estabilidade do estado tipado do LangGraph StateGraph.
    """

    def __init__(
        self,
        agent: Optional[MediFlowStateGraphAgent] = None,
        db_path: Optional[str] = None,
        storage_dir: Optional[str] = None,
    ) -> None:
        if agent:
            self.agent = agent
        else:
            resolved_storage_dir = storage_dir or os.path.join(tempfile.gettempdir(), "mediflow_load_storage")
            resolved_db = db_path or os.path.join(tempfile.gettempdir(), f"mediflow_load_{os.getpid()}.db")
            storage = OCIStorageServiceV3(
                bucket_name="mediflow-test-bucket",
                local_fallback_dir=resolved_storage_dir,
                db_path=resolved_db,
            )
            dispatcher = NotificationDispatcher(mock_mode=True)
            self.agent = MediFlowStateGraphAgent(
                storage_service=storage,
                notification_dispatcher=dispatcher,
            )

    @staticmethod
    def generate_synthetic_payloads(count: int) -> List[DocumentoClinicoInput]:
        """
        Gera uma amostra balanceada de documentos sintéticos alternando entre:
          - Rotina (Receituário Amoxicilina)
          - Urgência (Laudo TEP Agudo)
          - Ambiguidade / HitL (Rasura e ausência de CRM)
        """
        base_scenarios = [
            (
                "ROTINA",
                "CLINICA VIDA PLENA - RECEITUARIO MEDICO. Paciente: {nome}, {idade} anos. "
                "Solicitante: Dr. Henrique Almeida CRM-SP 198432. Diagnóstico: Amigdalite Bacteriana Aguda. "
                "Prescrição: Amoxicilina + Clavulanato 875/125mg, 1 comprimido de 12/12h por 7 dias.",
                "Ambulatorio",
            ),
            (
                "URGENCIA",
                "HOSPITAL SANTA LUCIA - LAUDO DE TOMOGRAFIA DE TORAX. Paciente: {nome}, {idade} anos. "
                "Solicitante: Dra. Renata Silveira CRM-SP 145892. "
                "Achados: Defeito de enchimento oclusivo em artéria pulmonar principal direita compatível com Tromboembolismo Pulmonar Agudo. "
                "Conclusão: Tromboembolismo Pulmonar Agudo (TEP) - Condição Crítica de Urgência.",
                "Pronto_Socorro",
            ),
            (
                "HITL",
                "RECEITA MEDICA - CLINICA CENTRAL. Paciente: {nome}... "
                "Prescrição: Metoprolol dosagem borrada ?? mg uso contínuo. "
                "Assinatura ilegível. CRM ausente ou ilegível.",
                "Ambulatorio",
            ),
        ]

        nomes = ["Mariana Silva", "Carlos Eduardo", "Roberto Fonseca", "Juliana Paes", "Lucas Moura", "Beatriz Ramos"]
        payloads: List[DocumentoClinicoInput] = []

        for i in range(count):
            tipo, template, canal = base_scenarios[i % len(base_scenarios)]
            nome = nomes[i % len(nomes)]
            idade = 20 + (i * 3) % 60
            texto = template.format(nome=nome, idade=idade)
            doc_id = f"LOAD-DOC-2026-{1000 + i}"

            payloads.append(
                DocumentoClinicoInput(
                    documento_id=doc_id,
                    tipo_arquivo=TipoArquivoEnum.TEXTO,
                    documento_texto=texto,
                    canal_origem=canal,
                )
            )

        return payloads

    def run_concurrency_test(
        self,
        concurrency: int = 10,
        max_workers: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Dispara requisições simultâneas em paralelo via ThreadPoolExecutor
        avaliando latência individual, total decorrido e taxa de sucesso.
        """
        payloads = self.generate_synthetic_payloads(concurrency)
        workers = max_workers or min(concurrency, 16)

        results: List[Dict[str, Any]] = []
        errors: List[str] = []

        def _execute_single(doc: DocumentoClinicoInput) -> Dict[str, Any]:
            t_start = time.perf_counter()
            try:
                output = self.agent.run(doc)
                latencia_ms = round((time.perf_counter() - t_start) * 1000, 2)
                return {
                    "documento_id": doc.documento_id,
                    "status": output.status,
                    "prioridade": output.classificacao.nivel_prioridade.value,
                    "destino": output.decisao_roteamento.destino_principal.value,
                    "requer_auditoria": output.decisao_roteamento.requer_auditoria_humana,
                    "latencia_ms": latencia_ms,
                    "sucesso": True,
                }
            except Exception as exc:
                latencia_ms = round((time.perf_counter() - t_start) * 1000, 2)
                return {
                    "documento_id": doc.documento_id,
                    "status": "erro_excecao",
                    "erro": str(exc),
                    "latencia_ms": latencia_ms,
                    "sucesso": False,
                }

        t_wall_start = time.perf_counter()

        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_doc = {executor.submit(_execute_single, doc): doc for doc in payloads}
            for future in concurrent.futures.as_completed(future_to_doc):
                res = future.result()
                results.append(res)
                if not res["sucesso"]:
                    errors.append(f"{res['documento_id']}: {res.get('erro')}")

        total_wall_time = max(0.001, time.perf_counter() - t_wall_start)
        latencias = [r["latencia_ms"] for r in results]

        total_sucesso = sum(1 for r in results if r["sucesso"])
        throughput_rps = round(concurrency / total_wall_time, 2) if total_wall_time > 0 else 0.0

        # Percentis
        sorted_lat = sorted(latencias)
        p50 = sorted_lat[int(len(sorted_lat) * 0.50)]
        p95 = sorted_lat[min(int(len(sorted_lat) * 0.95), len(sorted_lat) - 1)]
        p99 = sorted_lat[min(int(len(sorted_lat) * 0.99), len(sorted_lat) - 1)]

        sla_cumprido = sum(1 for l in latencias if l < 5000.0)
        taxa_sla = round((sla_cumprido / concurrency) * 100, 2)

        return {
            "concorrencia_testada": concurrency,
            "workers_alocados": workers,
            "tempo_total_segundos": round(total_wall_time, 2),
            "throughput_rps": throughput_rps,
            "requisicoes_com_sucesso": total_sucesso,
            "requisicoes_com_falha": len(errors),
            "taxa_sucesso_percentual": round((total_sucesso / concurrency) * 100, 2),
            "latencia_media_ms": round(sum(latencias) / len(latencias), 2) if latencias else 0.0,
            "latencia_min_ms": round(min(latencias), 2) if latencias else 0.0,
            "latencia_max_ms": round(max(latencias), 2) if latencias else 0.0,
            "p50_ms": p50,
            "p95_ms": p95,
            "p99_ms": p99,
            "cumprimento_sla_percentual": taxa_sla,
            "erros": errors,
        }
