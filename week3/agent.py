"""
MediFlow — Grafo de Decisão Condicional em LangGraph (StateGraph) & SRE (Release 1.3)
Hackathon ONE G10 — Oracle Next Education & Alura (Equipo 22)
Persona Responsável: Arquiteto Carlos Vance (Carlos Magno — Tech Lead, SRE/DevOps, IA & Python Core)
Integrações: Fernando Szekut (Webhooks), Helder (OCI & SQLite), Alessandro (FastAPI & QA)
"""

from __future__ import annotations

import datetime
import json
import logging
import os
import re
import sys
import time
from typing import Any, Callable, Dict, List, Optional, TypedDict

import httpx
from langgraph.graph import END, START, StateGraph

# Importação dos schemas oficiais da raiz
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from mediflow_schemas import (
    ArmazenamentoOCI,
    ClassificacaoDocumento,
    DadosExtraidos,
    DadosMedicoSolicitante,
    DadosPaciente,
    DecisaoRoteamento,
    DestinoRoteamentoEnum,
    DocumentoClinicoInput,
    NivelPrioridadeEnum,
    NotificacaoGerada,
    ResultadoTriagemOutput,
    TipoArquivoEnum,
)

from week3.notifications import NotificationDispatcher
from week3.storage import OCIStorageServiceV3

logger = logging.getLogger("mediflow.agent_v3")

CONFIDENCE_THRESHOLD_HITL = 0.85
SLA_MAX_LATENCY_MS = 5000.0

CRITICAL_EMERGENCY_FINDINGS = [
    ("tromboembolismo pulmonar", "Tromboembolismo Pulmonar Agudo (TEP)", "I26.9"),
    ("tep agudo", "Tromboembolismo Pulmonar Agudo (TEP)", "I26.9"),
    ("embolia pulmonar", "Tromboembolismo Pulmonar Agudo (TEP)", "I26.9"),
    ("infarto agudo do miocardio", "Infarto Agudo do Miocárdio (IAM)", "I21.9"),
    ("avc isquemico", "Acidente Vascular Cerebral Isquêmico Agudo", "I63.9"),
    ("sepse grave", "Sepse Grave / Choque Séptico", "A41.9"),
]


class MediFlowAgentState(TypedDict, total=False):
    """Estado tipado formal do Grafo de Decisão Condicional do LangGraph."""

    documento_input: DocumentoClinicoInput
    texto_normalizado: str
    classificacao: Optional[ClassificacaoDocumento]
    dados_extraidos: Optional[DadosExtraidos]
    decisao_roteamento: Optional[DecisaoRoteamento]
    armazenamento_oci: Optional[ArmazenamentoOCI]
    resultado_final: Optional[ResultadoTriagemOutput]
    telemetria_sre: Dict[str, Any]
    notificacao_webhook: Optional[Dict[str, Any]]


class MediFlowStateGraphAgent:
    """
    Agente Autônomo com StateGraph formal do LangGraph:
      [START]
         │
         ▼
      [ingestor_node]
         │
         ▼
      [classifier_extractor_node] (NVIDIA NIM Llama 3.2 11B / Fallback SRE)
         │
         ▼
      [validator_sre_check_node] (Pydantic v2 + Regras de Confiabilidade Clínica)
         │
         ├──► (Conditional Edge: Urgente, qualquer score) ──► [emergency_route_node] (Webhook; score < 0.85 também vai à revisão)
         ├──► (Conditional Edge: Rotina  & Score >= 0.85) ──► [routine_route_node]   (Farmácia / PEP)
         └──► (Conditional Edge: Score < 0.85 ou Ambíguo) ──► [hitl_route_node]      (Fila Revisão Humana)
                                                                      │
         ◄────────────────────────────────────────────────────────────┘
         ▼
      [oci_persistence_node] (Segregação OCI por Especialidade + SQLite Audit Log)
         │
         ▼
       [END]
    """

    def __init__(
        self,
        storage_service: Optional[OCIStorageServiceV3] = None,
        notification_dispatcher: Optional[NotificationDispatcher] = None,
    ) -> None:
        self.storage = storage_service or OCIStorageServiceV3()
        self.notifications = notification_dispatcher or NotificationDispatcher()

        self.nvidia_api_key = os.getenv("NVIDIA_API_KEY", "")
        self.nvidia_model = os.getenv("NVIDIA_MODEL", "meta/llama-3.2-11b-vision-instruct")
        self.nvidia_base_url = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")

        # Compilação formal do StateGraph
        self.graph = self._build_state_graph()
        self.compiled_app = self.graph.compile()

    def _call_nvidia_nim(self, doc: DocumentoClinicoInput, texto_normalizado: str) -> Optional[Dict[str, Any]]:
        """Invoca o modelo multimodal NVIDIA NIM com retentativas e timeout resiliente."""
        if not self.nvidia_api_key:
            return None

        prompt_sistema = (
            "Você é o especialista clínico e motor de IA do MediFlow (Hackathon ONE G10 - Equipo 22). "
            "Sua tarefa é analisar o documento clínico fornecido e extrair entidades estruturadas "
            "com máxima precisão médica, classificando o tipo do documento, prioridade e score de confiança. "
            "Retorne APENAS um objeto JSON válido, sem texto introdutório nem markdown, no formato:\n"
            "{\n"
            '  "tipo_documento": "ex: Laudo de Exame de Imagem | Receituário Médico | Guia TISS",\n'
            '  "especialidade": "ex: Radiologia / Pneumologia | Clínica Médica",\n'
            '  "nivel_prioridade": "Rotina | Alta | Urgente | Revisao_Humana",\n'
            '  "score_confianca_classificacao": 0.95,\n'
            '  "paciente": {"nome": "string ou null", "idade": number ou null},\n'
            '  "medico_solicitante": {"nome": "string ou null", "crm": "string ou null"},\n'
            '  "exame_realizado": "string ou null",\n'
            '  "diagnostico_principal": "string ou null",\n'
            '  "cid_sugerido": "string ou null",\n'
            '  "medicamentos_prescritos": ["string"]\n'
            "}\n"
            "Diretrizes clínicas essenciais:\n"
            "- Se identificar Tromboembolismo Pulmonar Agudo (TEP), Embolia Pulmonar, Infarto (IAM) ou quadro crítico, marque nivel_prioridade='Urgente', score_confianca_classificacao >= 0.95 e cid_sugerido='I26.9'.\n"
            "- Se o documento for manuscrito ilegível, faltar o CRM médico ou houver rasuras graves, marque nivel_prioridade='Revisao_Humana' e score_confianca_classificacao < 0.85."
        )

        user_content: Any
        if doc.arquivo_binario_b64 and doc.tipo_arquivo in (TipoArquivoEnum.IMAGEM, TipoArquivoEnum.PDF):
            b64_str = doc.arquivo_binario_b64
            url_img = b64_str if b64_str.startswith("data:") else f"data:image/jpeg;base64,{b64_str}"
            user_content = [
                {"type": "text", "text": f"Analise a imagem deste documento clínico:\n{texto_normalizado}"},
                {"type": "image_url", "image_url": {"url": url_img}},
            ]
        else:
            user_content = f"Analise o seguinte documento clínico:\n{texto_normalizado}"

        payload = {
            "model": self.nvidia_model,
            "messages": [
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": user_content},
            ],
            "temperature": 0.1,
            "top_p": 0.7,
            "max_tokens": 1024,
        }

        headers = {
            "Authorization": f"Bearer {self.nvidia_api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        url = f"{self.nvidia_base_url.rstrip('/')}/chat/completions"
        timeout = httpx.Timeout(60.0, connect=15.0, read=60.0)

        for attempt in range(2):
            try:
                with httpx.Client(timeout=timeout) as client:
                    resp = client.post(url, json=payload, headers=headers)
                    if resp.status_code == 200:
                        raw_content = resp.json()["choices"][0]["message"]["content"].strip()
                        if "```" in raw_content:
                            raw_content = re.sub(r"^```(?:json)?\s*", "", raw_content, flags=re.MULTILINE)
                            raw_content = re.sub(r"\s*```$", "", raw_content, flags=re.MULTILINE)
                        parsed = json.loads(raw_content.strip())
                        logger.info("Extração clínica concluída via NVIDIA NIM (%s)", self.nvidia_model)
                        return parsed
                    elif resp.status_code in (500, 502, 503, 504) and attempt == 0:
                        time.sleep(2.0)
                        continue
                    else:
                        break
            except Exception as exc:
                if attempt == 0:
                    time.sleep(2.0)
                    continue
                logger.warning("Falha ao comunicar com NVIDIA NIM (%s). Fallback SRE ativado.", exc)
                break
        return None

    # -------------------------------------------------------------------------
    # NÓ 1: Ingestão Multimodal
    # -------------------------------------------------------------------------
    def ingestor_node(self, state: MediFlowAgentState) -> MediFlowAgentState:
        t0 = time.time()
        doc = state["documento_input"]
        texto_norm = " ".join(doc.documento_texto.strip().split())
        state["texto_normalizado"] = texto_norm

        raw_path = self.storage.resolve_object_path(
            documento_id=doc.documento_id,
            requer_auditoria_humana=False,
            nivel_prioridade="Rotina",
            is_raw_ingestion=True,
        )
        self.storage.save_json_object(raw_path, doc.to_dict(exclude_none=True))

        telemetria = state.get("telemetria_sre", {})
        telemetria["ingestor_latencia_ms"] = round((time.time() - t0) * 1000, 2)
        telemetria["raw_path"] = raw_path
        state["telemetria_sre"] = telemetria
        return state

    # -------------------------------------------------------------------------
    # NÓ 2: Classificação e Extração com LLM / Heurística
    # -------------------------------------------------------------------------
    def classifier_extractor_node(self, state: MediFlowAgentState) -> MediFlowAgentState:
        t0 = time.time()
        texto = state["texto_normalizado"]
        doc = state["documento_input"]

        llm_data = self._call_nvidia_nim(doc, texto)
        telemetria = state.get("telemetria_sre", {})

        if llm_data and isinstance(llm_data, dict):
            telemetria["provider"] = f"NVIDIA NIM ({self.nvidia_model})"
            prioridade_str = str(llm_data.get("nivel_prioridade", "Rotina")).capitalize()
            prioridade_map = {
                "Rotina": NivelPrioridadeEnum.ROTINA,
                "Alta": NivelPrioridadeEnum.ALTA,
                "Urgente": NivelPrioridadeEnum.URGENTE,
                "Revisao_humana": NivelPrioridadeEnum.REVISAO_HUMANA,
                "Revisão_humana": NivelPrioridadeEnum.REVISAO_HUMANA,
            }
            nivel_prioridade = prioridade_map.get(prioridade_str, NivelPrioridadeEnum.ROTINA)
            score_confianca = float(llm_data.get("score_confianca_classificacao", 0.92))
            paciente_data = llm_data.get("paciente") or {}
            medico_data = llm_data.get("medico_solicitante") or {}

            state["classificacao"] = ClassificacaoDocumento(
                tipo_documento=str(llm_data.get("tipo_documento", "Documento Clínico")),
                especialidade=str(llm_data.get("especialidade", "Clínica Geral")),
                nivel_prioridade=nivel_prioridade,
                score_confianca_classificacao=min(1.0, max(0.0, score_confianca)),
            )
            state["dados_extraidos"] = DadosExtraidos(
                paciente=DadosPaciente(
                    nome=paciente_data.get("nome"),
                    idade=paciente_data.get("idade"),
                ),
                medico_solicitante=DadosMedicoSolicitante(
                    nome=medico_data.get("nome"),
                    crm=medico_data.get("crm"),
                ),
                exame_realizado=llm_data.get("exame_realizado"),
                diagnostico_principal=llm_data.get("diagnostico_principal"),
                cid_sugerido=llm_data.get("cid_sugerido"),
                medicamentos_prescritos=llm_data.get("medicamentos_prescritos") or None,
            )
        else:
            # Fallback Resiliente SRE
            telemetria["provider"] = "Heuristic Clinical Engine (Resilient SRE Fallback)"
            texto_lower = texto.lower()

            paciente_nome = None
            paciente_idade = None
            match_pac = re.search(r"Paciente:\s*([^,\.\n]+?)(?:,\s*(\d{1,3})\s*anos)?(?:\.|$|\s+Solicitante:|\s+M[eé]dico:)", texto, re.IGNORECASE)
            if match_pac:
                candidato = match_pac.group(1).strip()
                if "ilegivel" not in candidato.lower() and "rasurado" not in candidato.lower():
                    paciente_nome = candidato
                if match_pac.group(2):
                    paciente_idade = int(match_pac.group(2))

            medico_nome = None
            medico_crm = None
            match_med = re.search(r"(?:Solicitante|M[eé]dico):\s*(Dr[a]?\.\s*[^C\n,\.]+?)(?:\s+CRM[-:\s]*([A-Z]{2})?[-:\s]*(\d{4,7}))?(?:\.|$)", texto, re.IGNORECASE)
            if match_med:
                medico_nome = match_med.group(1).strip()
                uf = match_med.group(2)
                num_crm = match_med.group(3)
                medico_crm = f"{num_crm}-{uf.upper()}" if (num_crm and uf) else num_crm

            exame_realizado = None
            match_exame = re.search(r"Exame:\s*([^\.\n]+)", texto, re.IGNORECASE)
            if match_exame:
                exame_realizado = match_exame.group(1).strip()

            medicamentos = []
            match_presc = re.search(r"Prescri[cç][aã]o:\s*([^\.\n]+)", texto, re.IGNORECASE)
            if match_presc:
                medicamentos.append(match_presc.group(1).strip())

            tipo_doc = "Documento Clínico Geral"
            especialidade = "Clínica Médica"
            nivel_prioridade = NivelPrioridadeEnum.ROTINA
            score_confianca = 0.94
            diagnostico_principal = None
            cid_sugerido = None

            if "laudo" in texto_lower or "tomografia" in texto_lower or "radiologico" in texto_lower:
                tipo_doc = "Laudo de Exame de Imagem"
                especialidade = "Radiologia / Pneumologia"
            elif "receituario" in texto_lower or "receita" in texto_lower or "prescricao" in texto_lower:
                tipo_doc = "Receituário Médico"
                especialidade = "Clínica Médica / Ambulatorial"

            for termo, diag_padrao, cid_padrao in CRITICAL_EMERGENCY_FINDINGS:
                if termo in texto_lower:
                    nivel_prioridade = NivelPrioridadeEnum.URGENTE
                    diagnostico_principal = diag_padrao
                    cid_sugerido = cid_padrao
                    score_confianca = 0.99
                    break

            if not diagnostico_principal:
                match_diag = re.search(r"(?:Diagn[oó]stico|Indica[cç][aã]o|Conclus[aã]o):\s*([^\.\n]+)", texto, re.IGNORECASE)
                if match_diag:
                    diagnostico_principal = match_diag.group(1).strip()
                if "amigdalite" in texto_lower:
                    cid_sugerido = "J03.9"

            state["classificacao"] = ClassificacaoDocumento(
                tipo_documento=tipo_doc,
                especialidade=especialidade,
                nivel_prioridade=nivel_prioridade,
                score_confianca_classificacao=score_confianca,
            )
            state["dados_extraidos"] = DadosExtraidos(
                paciente=DadosPaciente(nome=paciente_nome, idade=paciente_idade),
                medico_solicitante=DadosMedicoSolicitante(nome=medico_nome, crm=medico_crm),
                exame_realizado=exame_realizado,
                diagnostico_principal=diagnostico_principal,
                cid_sugerido=cid_sugerido,
                medicamentos_prescritos=medicamentos if medicamentos else None,
            )

        telemetria["classifier_latencia_ms"] = round((time.time() - t0) * 1000, 2)
        state["telemetria_sre"] = telemetria
        return state

    # -------------------------------------------------------------------------
    # NÓ 3: Validação de Confiabilidade e Travas Clínicas SRE
    # -------------------------------------------------------------------------
    def validator_sre_check_node(self, state: MediFlowAgentState) -> MediFlowAgentState:
        t0 = time.time()
        classif = state["classificacao"]
        dados = state["dados_extraidos"]
        assert classif is not None and dados is not None

        texto_lower = state["texto_normalizado"].lower()
        penalidades = 0.0
        motivos = []

        if any(w in texto_lower for w in ["ilegivel", "ilegível", "rasurado", "borrado", "duvidoso", "??"]):
            penalidades += 0.35
            motivos.append("trechos ilegíveis ou rasurados detectados no documento")

        if not dados.paciente.nome:
            penalidades += 0.25
            motivos.append("identificação do paciente ausente")

        if not dados.medico_solicitante.crm:
            penalidades += 0.25
            motivos.append("registro CRM do médico solicitante ausente ou incompleto")

        if penalidades > 0:
            novo_score = max(0.15, round(classif.score_confianca_classificacao - penalidades, 2))
            classif.score_confianca_classificacao = novo_score
            # Dado faltando não apaga a urgência: o achado crítico continua indo para o plantão
            if novo_score < CONFIDENCE_THRESHOLD_HITL and classif.nivel_prioridade != NivelPrioridadeEnum.URGENTE:
                classif.nivel_prioridade = NivelPrioridadeEnum.REVISAO_HUMANA

        telemetria = state.get("telemetria_sre", {})
        telemetria["motivos_ambiguidade"] = motivos
        telemetria["validator_latencia_ms"] = round((time.time() - t0) * 1000, 2)
        state["telemetria_sre"] = telemetria
        return state

    # -------------------------------------------------------------------------
    # ARESTA CONDICIONAL: Roteamento
    # -------------------------------------------------------------------------
    @staticmethod
    def decide_route(state: MediFlowAgentState) -> str:
        classif = state["classificacao"]
        assert classif is not None
        score = classif.score_confianca_classificacao
        prioridade = classif.nivel_prioridade

        # Urgência antes do score: um TEP sem o nome do paciente não pode esperar na fila sem
        # alerta. Com score baixo, a rota de emergência também manda o documento à revisão humana.
        if prioridade == NivelPrioridadeEnum.URGENTE:
            return "emergency_route"
        if score < CONFIDENCE_THRESHOLD_HITL or prioridade == NivelPrioridadeEnum.REVISAO_HUMANA:
            return "hitl_route"
        return "routine_route"

    # -------------------------------------------------------------------------
    # NÓ 4A: Rota de Emergência Médica (Disparo de Webhook)
    # -------------------------------------------------------------------------
    def emergency_route_node(self, state: MediFlowAgentState) -> MediFlowAgentState:
        t0 = time.time()
        dados = state["dados_extraidos"]
        doc = state["documento_input"]
        classif = state["classificacao"]
        assert dados is not None and classif is not None

        diag = dados.diagnostico_principal or "Quadro Crítico Agudo"
        paciente = dados.paciente.nome or "Paciente Sintomático"
        crm = dados.medico_solicitante.crm or "CRM Não Especificado"

        notificacao = NotificacaoGerada(
            canal="Alerta_Plantao_Medico",
            mensagem=f"ALERTA URGENTE: {diag} para paciente {paciente} no Pronto-Socorro.",
        )

        justificativa = f"Achado crítico de alta gravidade ({diag}) detectado em paciente sintomático."
        score = classif.score_confianca_classificacao
        requer_revisao = score < CONFIDENCE_THRESHOLD_HITL
        if requer_revisao:
            motivos = state.get("telemetria_sre", {}).get("motivos_ambiguidade", [])
            motivos_str = "; ".join(motivos) if motivos else "score de confiança abaixo do threshold regulatório"
            justificativa += (
                f" Plantão avisado e documento enviado também à Auditoria Humana: {motivos_str} (score={score:.2f} < 0.85)."
            )

        state["decisao_roteamento"] = DecisaoRoteamento(
            destino_principal=DestinoRoteamentoEnum.FILA_EMERGENCIA_MEDICA,
            requer_auditoria_humana=requer_revisao,
            justificativa_roteamento=justificativa,
            notificacao_gerada=notificacao,
        )

        # Disparo do Webhook de emergência em tempo real (Fernando Nexus)
        webhook_res = self.notifications.dispatch_emergency_alert(
            documento_id=doc.documento_id,
            paciente_nome=paciente,
            diagnostico=diag,
            crm_solicitante=crm,
            canal="Alerta_Plantao_Medico",
            mensagem_customizada=notificacao.mensagem,
        )
        state["notificacao_webhook"] = webhook_res

        telemetria = state.get("telemetria_sre", {})
        telemetria["emergency_node_latencia_ms"] = round((time.time() - t0) * 1000, 2)
        state["telemetria_sre"] = telemetria
        return state

    # -------------------------------------------------------------------------
    # NÓ 4B: Rota de Rotina Aprovada
    # -------------------------------------------------------------------------
    def routine_route_node(self, state: MediFlowAgentState) -> MediFlowAgentState:
        t0 = time.time()
        classif = state["classificacao"]
        assert classif is not None

        destino = (
            DestinoRoteamentoEnum.FARMACIA_HOSPITALAR
            if classif.tipo_documento == "Receituário Médico"
            else DestinoRoteamentoEnum.PRONTUARIO_ELETRONICO_PEP
        )

        state["decisao_roteamento"] = DecisaoRoteamento(
            destino_principal=destino,
            requer_auditoria_humana=False,
            justificativa_roteamento=f"{classif.tipo_documento} validado com alta confiança (score >= 0.85); encaminhado automaticamente.",
        )

        telemetria = state.get("telemetria_sre", {})
        telemetria["routine_node_latencia_ms"] = round((time.time() - t0) * 1000, 2)
        state["telemetria_sre"] = telemetria
        return state

    # -------------------------------------------------------------------------
    # NÓ 4C: Rota de Human-in-the-Loop (Auditoria)
    # -------------------------------------------------------------------------
    def hitl_route_node(self, state: MediFlowAgentState) -> MediFlowAgentState:
        t0 = time.time()
        telemetria = state.get("telemetria_sre", {})
        motivos = telemetria.get("motivos_ambiguidade", [])
        score = state["classificacao"].score_confianca_classificacao if state.get("classificacao") else 0.5

        motivos_str = "; ".join(motivos) if motivos else "score de confiança abaixo do threshold regulatório"
        doc_id = state["documento_input"].documento_id

        notificacao = NotificacaoGerada(
            canal="Painel_Auditoria_HitL",
            mensagem=f"REVISÃO HUMANA NECESSÁRIA: Documento {doc_id} retido para validação do auditor ({motivos_str}).",
        )

        state["decisao_roteamento"] = DecisaoRoteamento(
            destino_principal=DestinoRoteamentoEnum.FILA_REVISAO_HUMANA,
            requer_auditoria_humana=True,
            justificativa_roteamento=f"Documento retido preventivamente para Auditoria Humana (Human-in-the-Loop): {motivos_str} (score={score:.2f} < 0.85).",
            notificacao_gerada=notificacao,
        )

        telemetria["hitl_node_latencia_ms"] = round((time.time() - t0) * 1000, 2)
        state["telemetria_sre"] = telemetria
        return state

    # -------------------------------------------------------------------------
    # NÓ 5: Persistência Dinâmica OCI & Log SQLite (Helder - Atlas Data)
    # -------------------------------------------------------------------------
    def oci_persistence_node(self, state: MediFlowAgentState) -> MediFlowAgentState:
        t0 = time.time()
        doc = state["documento_input"]
        classif = state["classificacao"]
        dados = state["dados_extraidos"]
        decisao = state["decisao_roteamento"]
        telemetria = state.get("telemetria_sre", {})

        assert classif is not None and dados is not None and decisao is not None

        # Segregação dinâmica por especialidade clínica
        object_path = self.storage.resolve_object_path(
            documento_id=doc.documento_id,
            requer_auditoria_humana=decisao.requer_auditoria_humana,
            nivel_prioridade=classif.nivel_prioridade.value,
            especialidade=classif.especialidade,
        )

        armazenamento_info = ArmazenamentoOCI(
            bucket=self.storage.bucket_name,
            caminho_objeto=object_path,
            status_backup="sucesso",
        )

        # Só a fila de revisão retém o documento; a emergência com revisão já avisou o plantão
        retido = decisao.destino_principal == DestinoRoteamentoEnum.FILA_REVISAO_HUMANA
        status_doc = "retido_auditoria_humana" if retido else "processado"

        resultado = ResultadoTriagemOutput(
            status=status_doc,
            documento_id=doc.documento_id,
            classificacao=classif,
            dados_extraidos=dados,
            decisao_roteamento=decisao,
            armazenamento_oci=armazenamento_info,
        )

        # Gravação no Object Storage (com espelho local)
        self.storage.save_json_object(object_path, resultado.to_dict(exclude_none=True))

        # Gravação no histórico transacional do SQLite
        provedor = telemetria.get("provider", "Heuristic Engine")
        latencia_total = sum(v for k, v in telemetria.items() if k.endswith("_latencia_ms")) + round((time.time() - t0) * 1000, 2)

        self.storage.log_triage_decision(
            documento_id=doc.documento_id,
            tipo_documento=classif.tipo_documento,
            especialidade=classif.especialidade,
            prioridade=classif.nivel_prioridade.value,
            score_confianca=classif.score_confianca_classificacao,
            paciente_nome=dados.paciente.nome,
            medico_crm=dados.medico_solicitante.crm,
            diagnostico_principal=dados.diagnostico_principal,
            destino_principal=decisao.destino_principal.value,
            requer_auditoria=decisao.requer_auditoria_humana,
            caminho_oci=object_path,
            provedor_ia=provedor,
            status_final=status_doc,
            latencia_ms=latencia_total,
        )

        telemetria["oci_node_latencia_ms"] = round((time.time() - t0) * 1000, 2)
        telemetria["latencia_total_ms"] = latencia_total
        telemetria["sla_cumprido"] = latencia_total < SLA_MAX_LATENCY_MS

        state["armazenamento_oci"] = armazenamento_info
        state["resultado_final"] = resultado
        state["telemetria_sre"] = telemetria
        return state

    # -------------------------------------------------------------------------
    # Construtor do StateGraph no LangGraph
    # -------------------------------------------------------------------------
    def _build_state_graph(self) -> StateGraph:
        graph = StateGraph(MediFlowAgentState)

        graph.add_node("ingestor", self.ingestor_node)
        graph.add_node("classifier_extractor", self.classifier_extractor_node)
        graph.add_node("validator_sre_check", self.validator_sre_check_node)
        graph.add_node("emergency_route", self.emergency_route_node)
        graph.add_node("routine_route", self.routine_route_node)
        graph.add_node("hitl_route", self.hitl_route_node)
        graph.add_node("oci_persistence", self.oci_persistence_node)

        graph.add_edge(START, "ingestor")
        graph.add_edge("ingestor", "classifier_extractor")
        graph.add_edge("classifier_extractor", "validator_sre_check")

        graph.add_conditional_edges(
            "validator_sre_check",
            self.decide_route,
            {
                "emergency_route": "emergency_route",
                "routine_route": "routine_route",
                "hitl_route": "hitl_route",
            },
        )

        graph.add_edge("emergency_route", "oci_persistence")
        graph.add_edge("routine_route", "oci_persistence")
        graph.add_edge("hitl_route", "oci_persistence")
        graph.add_edge("oci_persistence", END)

        return graph

    def run(self, documento_input: DocumentoClinicoInput) -> ResultadoTriagemOutput:
        """Executa a triagem completa compilada no StateGraph do LangGraph."""
        initial_state: MediFlowAgentState = {
            "documento_input": documento_input,
            "telemetria_sre": {"timestamp_inicio": datetime.datetime.now().isoformat()},
        }
        final_state = self.compiled_app.invoke(initial_state)
        res = final_state.get("resultado_final")
        assert res is not None, "O grafo LangGraph falhou em produzir um resultado final."
        return res

    @staticmethod
    def get_graph_mermaid() -> str:
        """Retorna o diagrama de fluxo do Grafo LangGraph em formato Mermaid."""
        return (
            "flowchart TD\n"
            "    START([START]) --> Ingestor[IngestorNode / Backup Bruto]\n"
            "    Ingestor --> Classifier[ClassifierExtractorNode / NVIDIA NIM Llama 3.2 11B Vision]\n"
            "    Classifier --> Validator[ValidatorSRECheckNode / Pydantic v2]\n"
            "    Validator --> Router{Decisão Condicional}\n"
            "    Router -- 'Urgência, qualquer score' --> Emergency[EmergencyRouteNode / Webhook Plantão]\n"
            "    Router -- 'Rotina & Score >= 0.85' --> Routine[RoutineRouteNode / Farmácia & PEP]\n"
            "    Router -- 'Score < 0.85 ou Ambíguo' --> HitL[HumanInTheLoopNode / Auditoria Humana]\n"
            "    Emergency --> Storage[OCIPersistenceNode / Segregação por Especialidade & SQLite]\n"
            "    Routine --> Storage\n"
            "    HitL --> Storage\n"
            "    Storage --> END_NODE([END])\n"
        )


# =============================================================================
# Cenários de Teste Oficiais
# =============================================================================
SCENARIO_1_ROUTINE = DocumentoClinicoInput(
    documento_id="DOC-CLIN-2026-1001",
    tipo_arquivo=TipoArquivoEnum.PDF,
    documento_texto=(
        "CLINICA VIDA PLENA - RECEITUARIO MEDICO. Paciente: Mariana Costa Souza, 34 anos. "
        "Solicitante: Dr. Henrique Almeida CRM-SP 198432. Diagnóstico: Amigdalite Bacteriana Aguda. "
        "Prescrição: Amoxicilina + Clavulanato 875/125mg, 1 comprimido de 12/12h por 7 dias."
    ),
    canal_origem="Ambulatorio",
)

SCENARIO_2_URGENCY_TEP = DocumentoClinicoInput(
    documento_id="DOC-CLIN-2026-8942",
    tipo_arquivo=TipoArquivoEnum.PDF,
    documento_texto=(
        "HOSPITAL SANTA LUCIA - LAUDO DE EXAME RADIOLOGICO. Paciente: Carlos Eduardo Mendes, 52 anos. "
        "Solicitante: Dra. Renata Silveira CRM-SP 145892. Exame: Tomografia de Torax com contraste. "
        "Indicacao: Suspeita de embolia pulmonar aguda, dispneia subita. Achados: Falha de enchimento "
        "em arteria pulmonar principal direita compativel com TEP agudo. CONCLUSÃO: Quadro compativel "
        "com Tromboembolismo Pulmonar Agudo. Sugere-se correlacao clinica urgente."
    ),
    canal_origem="Pronto_Socorro",
)

SCENARIO_3_AMBIGUOUS_HITL = DocumentoClinicoInput(
    documento_id="DOC-CLIN-2026-5503",
    tipo_arquivo=TipoArquivoEnum.IMAGEM,
    documento_texto=(
        "RECEITUARIO MANUSCRITO DIGITALIZADO. Paciente: Roberto F. [rasurado / ilegível]. "
        "Solicitante: Dr. Plantonista (CRM ausente / ilegível). "
        "Prescrição: Metoprolol dosagem borrada ?? mg uso contínuo."
    ),
    canal_origem="Triagem_Externa",
)


if __name__ == "__main__":
    agent = MediFlowStateGraphAgent()
    print("🏥 Executando Agente LangGraph StateGraph (Release 1.3)...")
    for doc in (SCENARIO_1_ROUTINE, SCENARIO_2_URGENCY_TEP, SCENARIO_3_AMBIGUOUS_HITL):
        print("=" * 70)
        res = agent.run(doc)
        print(f"ID: {res.documento_id} | Prioridade: {res.classificacao.nivel_prioridade.value} | Destino: {res.decisao_roteamento.destino_principal.value}")
        print(f"OCI Path: {res.armazenamento_oci.caminho_objeto}")

