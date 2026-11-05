"""
MediFlow — Motor de Telemetria de Produção e Métricas de SLA SRE (Release 1.4)
Hackathon ONE G10 — Oracle Next Education & Alura (Equipo 22)
Persona Responsável: Arquiteto Carlos Vance (Carlos Magno — Tech Lead & Líder SRE/DevOps)
"""

from __future__ import annotations

import json
import logging
import math
import os
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("mediflow.sre_telemetry")

SLA_MAX_LATENCY_MS = 5000.0  # Meta máxima de tempo de resposta: 5 segundos
AVAILABILITY_TARGET = 0.999   # SLA de disponibilidade clínica: 99.9% ("Três Noves")


class SRETelemetryEngine:
    """
    Motor SRE de cálculo estatístico de confiabilidade, percentis de latência,
    orçamento de erro (Error Budget) e conformidade de SLAs clínicos.
    """

    def __init__(self, db_path: str | Path = "./mediflow_audit.db") -> None:
        self.db_path = Path(db_path)

    @staticmethod
    def calculate_percentile(data: List[float], percentile: float) -> float:
        """
        Calcula o percentil exato com interpolação linear padrão.
        """
        if not data:
            return 0.0
        sorted_data = sorted(data)
        n = len(sorted_data)
        if n == 1:
            return sorted_data[0]
        
        index = (n - 1) * (percentile / 100.0)
        lower = math.floor(index)
        upper = math.ceil(index)
        weight = index - lower
        return round(sorted_data[lower] * (1.0 - weight) + sorted_data[upper] * weight, 2)

    def collect_metrics_from_records(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Processa uma lista de registros de triagem clínica e calcula métricas completas SRE.
        """
        total_requests = len(records)
        if total_requests == 0:
            return {
                "total_requisicoes": 0,
                "status_geral": "SEM_DADOS",
                "latencias_ms": {
                    "min": 0.0,
                    "media": 0.0,
                    "max": 0.0,
                    "p50": 0.0,
                    "p75": 0.0,
                    "p90": 0.0,
                    "p95": 0.0,
                    "p99": 0.0,
                },
                "sla": {
                    "limite_max_ms": SLA_MAX_LATENCY_MS,
                    "requisicoes_em_sla": 0,
                    "taxa_cumprimento_sla_percentual": 100.0,
                },
                "error_budget": {
                    "sla_disponibilidade_alvo": f"{AVAILABILITY_TARGET * 100:.1f}%",
                    "erros_permitidos": 0.0,
                    "falhas_reais": 0,
                    "error_budget_restante_percentual": 100.0,
                    "status_resiliencia": "NORMAL",
                },
                "distribuicao_provedor": {},
                "distribuicao_prioridade": {},
            }

        latencias = [float(r.get("latencia_ms", 0.0)) for r in records if r.get("latencia_ms") is not None]
        if not latencias:
            latencias = [0.0]

        lat_min = round(min(latencias), 2)
        lat_max = round(max(latencias), 2)
        lat_media = round(sum(latencias) / len(latencias), 2)

        p50 = self.calculate_percentile(latencias, 50.0)
        p75 = self.calculate_percentile(latencias, 75.0)
        p90 = self.calculate_percentile(latencias, 90.0)
        p95 = self.calculate_percentile(latencias, 95.0)
        p99 = self.calculate_percentile(latencias, 99.0)

        # Cálculo de cumprimento do SLA de Latência (< 5000ms)
        em_sla = sum(1 for l in latencias if l <= SLA_MAX_LATENCY_MS)
        taxa_sla = round((em_sla / total_requests) * 100, 2)

        # Cálculo de Orçamento de Erro (Error Budget)
        # Falha = status 'falha' ou status HTTP de erro
        falhas_reais = sum(1 for r in records if "falha" in str(r.get("status_final", "")).lower() or "erro" in str(r.get("status_final", "")).lower())
        erros_permitidos = round(total_requests * (1.0 - AVAILABILITY_TARGET), 4)

        if erros_permitidos > 0:
            consumo_budget = (falhas_reais / erros_permitidos) * 100
            budget_restante = max(0.0, round(100.0 - consumo_budget, 2))
        else:
            budget_restante = 100.0 if falhas_reais == 0 else 0.0

        if budget_restante > 50.0:
            status_resiliencia = "EXCELENTE (Budget Saudável)"
        elif budget_restante > 10.0:
            status_resiliencia = "ALERTA (Budget em Consumo)"
        else:
            status_resiliencia = "CRÍTICO (Budget Esgotado)"

        # Distribuição de Provedores de IA
        provedores: Dict[str, int] = {}
        for r in records:
            prov = r.get("provedor_ia") or "Desconhecido"
            provedores[prov] = provedores.get(prov, 0) + 1

        # Distribuição por Nível de Prioridade
        prioridades: Dict[str, int] = {}
        for r in records:
            prio = r.get("prioridade") or "Nao_Identificada"
            prioridades[prio] = prioridades.get(prio, 0) + 1

        return {
            "total_requisicoes": total_requests,
            "status_geral": "OPERACIONAL" if taxa_sla >= 95.0 else "DEGRADADO",
            "latencias_ms": {
                "min": lat_min,
                "media": lat_media,
                "max": lat_max,
                "p50": p50,
                "p75": p75,
                "p90": p90,
                "p95": p95,
                "p99": p99,
            },
            "sla": {
                "limite_max_ms": SLA_MAX_LATENCY_MS,
                "requisicoes_em_sla": em_sla,
                "taxa_cumprimento_sla_percentual": taxa_sla,
            },
            "error_budget": {
                "sla_disponibilidade_alvo": f"{AVAILABILITY_TARGET * 100:.1f}%",
                "erros_permitidos": erros_permitidos,
                "falhas_reais": falhas_reais,
                "error_budget_restante_percentual": budget_restante,
                "status_resiliencia": status_resiliencia,
            },
            "distribuicao_provedor": provedores,
            "distribuicao_prioridade": prioridades,
            "timestamp_coleta": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

    def collect_from_sqlite(self, limit: int = 200) -> Dict[str, Any]:
        """
        Consulta os registros da tabela SQLite de auditoria e calcula métricas consolidadas.
        """
        if not self.db_path.exists():
            return self.collect_metrics_from_records([])

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, documento_id, prioridade, status_final, latencia_ms, provedor_ia
                    FROM triagem_audit_log
                    ORDER BY id DESC LIMIT ?
                """, (limit,))
                rows = [dict(r) for r in cursor.fetchall()]
                return self.collect_metrics_from_records(rows)
        except Exception as exc:
            logger.warning("Falha ao ler métricas do SQLite (%s)", exc)
            return self.collect_metrics_from_records([])

    def export_metrics_json(self, output_path: str | Path = "./telemetria_producao_sre.json") -> Path:
        """
        Exporta o relatório consolidado de telemetria e SLAs em formato JSON.
        """
        metrics = self.collect_from_sqlite()
        path = Path(output_path)
        path.write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")
        logger.info("Relatório SRE consolidado exportado em: %s", path)
        return path

