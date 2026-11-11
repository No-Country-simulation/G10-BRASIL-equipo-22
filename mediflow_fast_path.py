"""
MediFlow — Motor de Fast-Path Heurístico & Otimização de Prompts (Sprint M5 - CARD-26)
Hackathon ONE G10 — Oracle Next Education & Alura (Equipo 22)
Persona Responsável: Arquiteto Carlos Vance (Carlos Magno — Tech Lead, SRE/DevOps, IA & Python Core)

Este módulo implementa:
1. Fast-Path Heurístico Ultrarrápido (< 100ms):
   Extrai entidades estruturadas e classifica documentos clínicos padronizados
   sem overhead de rede ou invocação de LLM externo quando os padrões são claros.
2. Prompt Compacto Otimizado (< 300 tokens):
   Redução drástica do payload de prompt de sistema para LLMs multimodais
   (NVIDIA NIM / Gemini), reduzindo o tempo de decodificação e latência média (< 3s).
3. Telemetria comparativa de latência e taxa de acerto do Fast-Path.
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from mediflow_schemas import (
    ClassificacaoDocumento,
    DadosExtraidos,
    DadosMedicoSolicitante,
    DadosPaciente,
    NivelPrioridadeEnum,
)

logger = logging.getLogger("mediflow.fast_path")

# =============================================================================
# PROMPT COMPACTO OTIMIZADO (< 300 TOKENS)
# =============================================================================
COMPACT_SYSTEM_PROMPT = (
    "Extraia entidades do documento clínico em JSON estrito (sem markdown):\n"
    "{"
    '"tipo_documento":"Laudo de Exame de Imagem|Receituário Médico|Guia TISS|Documento Clínico",'
    '"especialidade":"Radiologia / Pneumologia|Clínica Médica|etc",'
    '"nivel_prioridade":"Rotina|Alta|Urgente|Revisao_Humana",'
    '"score_confianca_classificacao":0.95,'
    '"paciente":{"nome":"str|null","idade":int|null},'
    '"medico_solicitante":{"nome":"str|null","crm":"str|null"},'
    '"exame_realizado":"str|null","diagnostico_principal":"str|null",'
    '"cid_sugerido":"str|null","medicamentos_prescritos":["str"]'
    "}\n"
    "Regras: Urgente se TEP/Embolia (I26.9), IAM (I21.9), AVC (I63.9), Sepse (A41.9). "
    "Revisao_Humana e score < 0.85 se ilegível/sem CRM/rasuras."
)

# Patologias Críticas de Emergência Hospitalar
CRITICAL_EMERGENCY_FINDINGS: List[Tuple[str, str, str]] = [
    ("tromboembolismo pulmonar", "Tromboembolismo Pulmonar Agudo (TEP)", "I26.9"),
    ("tep agudo", "Tromboembolismo Pulmonar Agudo (TEP)", "I26.9"),
    ("embolia pulmonar", "Tromboembolismo Pulmonar Agudo (TEP)", "I26.9"),
    ("infarto agudo do miocardio", "Infarto Agudo do Miocárdio (IAM)", "I21.9"),
    ("infarto agudo do miocárdio", "Infarto Agudo do Miocárdio (IAM)", "I21.9"),
    ("iam agudo", "Infarto Agudo do Miocárdio (IAM)", "I21.9"),
    ("avc isquemico", "Acidente Vascular Cerebral Isquêmico Agudo", "I63.9"),
    ("avc isquêmico", "Acidente Vascular Cerebral Isquêmico Agudo", "I63.9"),
    ("avc hemorragico", "Acidente Vascular Cerebral Hemorrágico", "I61.9"),
    ("avc hemorrágico", "Acidente Vascular Cerebral Hemorrágico", "I61.9"),
    ("sepse grave", "Sepse Grave / Choque Séptico", "A41.9"),
    ("choque septico", "Sepse Grave / Choque Séptico", "A41.9"),
    ("choque séptico", "Sepse Grave / Choque Séptico", "A41.9"),
    ("pneumotorax hipertensivo", "Pneumotórax Hipertensivo", "J93.0"),
    ("pneumotórax hipertensivo", "Pneumotórax Hipertensivo", "J93.0"),
]

# Expressões regulares pré-compiladas de alta performance (Fast-Path)
RE_PACIENTE = re.compile(
    r"Paciente:\s*([^,\.\n]+?)(?:,\s*(\d{1,3})\s*anos)?(?:\.|$|\s+Solicitante:|\s+M[eé]dico:|\s+Data:|\s+Conv[eê]nio:)",
    re.IGNORECASE,
)
RE_MEDICO_CRM = re.compile(
    r"(?:Solicitante|M[eé]dico|Dr[a]?\.):\s*(Dr[a]?\.?\s*[^C\n,\.]+?)?(?:\s+CRM[-:\s]*([A-Z]{2})?[-:\s]*(\d{4,7})(?:-([A-Z]{2}))?)?(?:\.|$|\s+Data:)",
    re.IGNORECASE,
)
RE_EXAME = re.compile(r"Exame:\s*([^\.\n]+)", re.IGNORECASE)
RE_PRESCRICAO = re.compile(r"(?:Prescri[cç][aã]o|Medicamento|Uso):\s*([^\.\n]+)", re.IGNORECASE)
RE_DIAGNOSTICO = re.compile(r"(?:Diagn[oó]stico|Indica[cç][aã]o|Conclus[aã]o|Hip[oó]tese):\s*([^\.\n]+)", re.IGNORECASE)
RE_ILEGIVEL = re.compile(r"\b(ilegivel|ilegível|rasurado|borrado|duvidoso|\?\?)\b", re.IGNORECASE)


@dataclass
class FastPathResult:
    """Resultado da execução do Fast-Path Heurístico."""

    is_fast_path: bool
    classificacao: ClassificacaoDocumento
    dados_extraidos: DadosExtraidos
    latencia_ms: float
    score_confianca: float
    motivos: List[str] = field(default_factory=list)


class FastPathEngine:
    """
    Motor Heurístico Determinístico de Alta Performance para Documentos Clínicos.
    Projetado para reduzir a latência de inferência para < 100ms em fluxos padronizados.
    """

    def __init__(self, confidence_threshold: float = 0.85) -> None:
        self.confidence_threshold = confidence_threshold

    def process(self, texto: str) -> FastPathResult:
        """
        Executa a extração em tempo ultra-baixo utilizando autômatos regex pré-compilados.
        Retorna FastPathResult com latência medida em milissegundos.
        """
        t_start = time.perf_counter()
        texto_limpo = " ".join(texto.strip().split())
        texto_lower = texto_limpo.lower()
        motivos: List[str] = []

        # 1. Verificação de Ambiguidade / Ilegibilidade
        tem_ilegivel = bool(RE_ILEGIVEL.search(texto_lower))
        if tem_ilegivel:
            motivos.append("trechos ilegíveis ou rasurados detectados no documento")

        # 2. Extração de Paciente
        paciente_nome: Optional[str] = None
        paciente_idade: Optional[int] = None
        match_pac = RE_PACIENTE.search(texto_limpo)
        if match_pac:
            candidato = match_pac.group(1).strip()
            if not RE_ILEGIVEL.search(candidato):
                paciente_nome = candidato
            if match_pac.group(2):
                try:
                    paciente_idade = int(match_pac.group(2))
                except ValueError:
                    pass

        # 3. Extração de Médico Solicitante e CRM
        medico_nome: Optional[str] = None
        medico_crm: Optional[str] = None
        match_med = RE_MEDICO_CRM.search(texto_limpo)
        if match_med:
            if match_med.group(1):
                nome_cand = match_med.group(1).strip()
                if not RE_ILEGIVEL.search(nome_cand):
                    medico_nome = nome_cand
            uf1 = match_med.group(2)
            num_crm = match_med.group(3)
            uf2 = match_med.group(4)
            uf = uf1 or uf2
            if num_crm and uf:
                medico_crm = f"{num_crm}-{uf.upper()}"
            elif num_crm:
                medico_crm = num_crm

        # 4. Extração de Exame e Prescrição
        exame_realizado: Optional[str] = None
        match_ex = RE_EXAME.search(texto_limpo)
        if match_ex:
            exame_realizado = match_ex.group(1).strip()

        medicamentos: List[str] = []
        match_presc = RE_PRESCRICAO.search(texto_limpo)
        if match_presc:
            medicamentos.append(match_presc.group(1).strip())

        # 5. Classificação de Tipologia e Especialidade
        tipo_documento = "Documento Clínico Geral"
        especialidade = "Clínica Médica"
        nivel_prioridade = NivelPrioridadeEnum.ROTINA
        score_confianca = 0.95
        diagnostico_principal: Optional[str] = None
        cid_sugerido: Optional[str] = None

        if any(k in texto_lower for k in ["laudo", "tomografia", "radiologico", "radiológico", "ressonancia", "ressonância", "raio-x"]):
            tipo_documento = "Laudo de Exame de Imagem"
            especialidade = "Radiologia / Pneumologia"
        elif any(k in texto_lower for k in ["receituario", "receituário", "receita", "prescricao", "prescrição", "uso oral"]):
            tipo_documento = "Receituário Médico"
            especialidade = "Clínica Médica / Ambulatorial"
        elif any(k in texto_lower for k in ["guia", "tiss", "autorizacao", "autorização", "procedimento"]):
            tipo_documento = "Guia de Solicitação de Procedimento (TISS)"
            especialidade = "Auditoria Médica"
        elif any(k in texto_lower for k in ["atestado", "repouso", "afastamento"]):
            tipo_documento = "Atestado Médico"
            especialidade = "Medicina do Trabalho"

        # 6. Detecção de Urgências Críticas Hospitalares (Prioridade Vital)
        achado_critico = False
        for termo, diag_padrao, cid_padrao in CRITICAL_EMERGENCY_FINDINGS:
            if termo in texto_lower:
                nivel_prioridade = NivelPrioridadeEnum.URGENTE
                diagnostico_principal = diag_padrao
                cid_sugerido = cid_padrao
                score_confianca = 0.99
                achado_critico = True
                break

        # 7. Diagnóstico e CID para Casos Não Críticos
        if not achado_critico:
            match_diag = RE_DIAGNOSTICO.search(texto_limpo)
            if match_diag:
                diagnostico_principal = match_diag.group(1).strip()
            if "amigdalite" in texto_lower or "faringite" in texto_lower:
                cid_sugerido = "J03.9"
            elif "hipertensao" in texto_lower or "hipertensão" in texto_lower:
                cid_sugerido = "I10"
            elif "diabetes" in texto_lower:
                cid_sugerido = "E11"
            elif "asma" in texto_lower or "bronquite" in texto_lower:
                cid_sugerido = "J45"

        # 8. Score Inicial de Classificação (Penalidades Clínicas)
        if achado_critico:
            score_confianca = 0.99
        elif tem_ilegivel:
            score_confianca = 0.60
            if nivel_prioridade != NivelPrioridadeEnum.URGENTE:
                nivel_prioridade = NivelPrioridadeEnum.REVISAO_HUMANA
        else:
            score_confianca = 0.95
            if not paciente_nome:
                score_confianca -= 0.25
            if not medico_crm:
                score_confianca -= 0.25
            score_confianca = round(max(0.15, min(1.0, score_confianca)), 2)
            if score_confianca < self.confidence_threshold and nivel_prioridade != NivelPrioridadeEnum.URGENTE:
                nivel_prioridade = NivelPrioridadeEnum.REVISAO_HUMANA

        if not paciente_nome:
            motivos.append("identificação do paciente ausente")
        if not medico_crm:
            motivos.append("registro CRM do médico ausente ou incompleto")

        # Elegibilidade para Fast-Path:
        # Documentos estruturados com alta confiança, achados críticos ou rasuras evidentes
        is_fast_path = bool(
            achado_critico
            or tem_ilegivel
            or (score_confianca >= self.confidence_threshold and paciente_nome is not None and medico_crm is not None)
            or (score_confianca >= self.confidence_threshold and bool(medicamentos) and paciente_nome is not None)
        )

        classificacao = ClassificacaoDocumento(
            tipo_documento=tipo_documento,
            especialidade=especialidade,
            nivel_prioridade=nivel_prioridade,
            score_confianca_classificacao=score_confianca,
        )

        dados_extraidos = DadosExtraidos(
            paciente=DadosPaciente(nome=paciente_nome, idade=paciente_idade),
            medico_solicitante=DadosMedicoSolicitante(nome=medico_nome, crm=medico_crm),
            exame_realizado=exame_realizado,
            diagnostico_principal=diagnostico_principal,
            cid_sugerido=cid_sugerido,
            medicamentos_prescritos=medicamentos if medicamentos else None,
        )

        t_end = time.perf_counter()
        latencia_ms = round((t_end - t_start) * 1000, 2)

        return FastPathResult(
            is_fast_path=is_fast_path,
            classificacao=classificacao,
            dados_extraidos=dados_extraidos,
            latencia_ms=latencia_ms,
            score_confianca=score_confianca,
            motivos=motivos,
        )


def estimate_prompt_tokens(prompt: str) -> int:
    """
    Estimativa rápida e determinística da contagem de tokens para texto em português.
    Aproximação padrão: 1 token ~ 3.8 caracteres para vocabulário técnico/português.
    """
    return max(1, int(len(prompt) / 3.8))
