"""
MediFlow — Core Data Contracts & Pydantic Schemas (Compatível com Pydantic v1 e v2)
Hackathon ONE G10 — Oracle Next Education & Alura (Equipo 22)
Personas:
  - Arquiteto Carlos Vance (Carlos): Tech Lead, Líder SRE/DevOps, Arquitetura IA & Python
  - Fernando Nexus (Fernando Szekut): Engenheiro de Integração de Agentes, Frontend/UX & Workflows
  - Atlas Data (Helder): Banco de Dados & Persistência OCI Always Free
  - Marcus Builder (Alessandro): Desenvolvedor Backend FastAPI, HitL & QA
"""

from __future__ import annotations

import json
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class _CompatBaseModel(BaseModel):
    """Garante compatibilidade transparente entre Pydantic v1 e Pydantic v2."""

    def to_dict(self, exclude_none: bool = True) -> Dict[str, Any]:
        if hasattr(self, "model_dump"):
            return self.model_dump(mode="json", exclude_none=exclude_none)  # type: ignore[attr-defined]
        raw = self.json(exclude_none=exclude_none)
        return json.loads(raw)


class TipoArquivoEnum(str, Enum):
    PDF = "PDF"
    IMAGEM = "IMAGEM"
    TEXTO = "TEXTO"
    JSON = "JSON"


class NivelPrioridadeEnum(str, Enum):
    ROTINA = "Rotina"
    ALTA = "Alta"
    URGENTE = "Urgente"
    REVISAO_HUMANA = "Revisao_Humana"


class DestinoRoteamentoEnum(str, Enum):
    FILA_EMERGENCIA_MEDICA = "Fila_Emergencia_Medica"
    FARMACIA_HOSPITALAR = "Farmacia_Hospitalar"
    PRONTUARIO_ELETRONICO_PEP = "Prontuario_Eletronico_PEP"
    AUDITORIA_AUTORIZACOES_TISS = "Auditoria_Autorizacoes_TISS"
    FILA_REVISAO_HUMANA = "Fila_Revisao_Humana"


class DocumentoClinicoInput(_CompatBaseModel):
    """Contrato de entrada para ingestão de documentos clínicos no MediFlow."""

    documento_id: str = Field(
        ...,
        description="Identificador único do documento clínico (ex.: DOC-CLIN-2026-8942)",
    )
    tipo_arquivo: TipoArquivoEnum = Field(
        default=TipoArquivoEnum.PDF,
        description="Formato do documento recebido (PDF, IMAGEM, TEXTO, JSON)",
    )
    documento_texto: str = Field(
        ...,
        min_length=5,
        description="Conteúdo textual extraído ou transcrição OCR/Multimodal do documento clínico",
    )
    arquivo_binario_b64: Optional[str] = Field(
        default=None,
        description="Conteúdo binário opcional em Base64 para PDFs ou imagens escaneadas",
    )
    canal_origem: str = Field(
        default="Pronto_Socorro",
        description="Canal hospitalar de origem (ex.: Pronto_Socorro, Ambulatorio, Internacao)",
    )


class ClassificacaoDocumento(_CompatBaseModel):
    """Metadados de classificação clínica e confiabilidade da extração."""

    tipo_documento: str = Field(
        ...,
        description="Categoria clínica identificada (ex.: Laudo de Exame de Imagem, Receituário Médico, Guia TISS)",
    )
    especialidade: str = Field(
        ...,
        description="Especialidade médica associada (ex.: Radiologia / Pneumologia, Clínica Médica)",
    )
    nivel_prioridade: NivelPrioridadeEnum = Field(
        ...,
        description="Nível de prioridade clínica calculado pelo agente",
    )
    score_confianca_classificacao: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Score de confiabilidade da extração entre 0.00 e 1.00",
    )


class DadosPaciente(_CompatBaseModel):
    nome: Optional[str] = Field(default=None, description="Nome completo do paciente")
    idade: Optional[int] = Field(default=None, ge=0, le=130, description="Idade do paciente em anos")


class DadosMedicoSolicitante(_CompatBaseModel):
    nome: Optional[str] = Field(default=None, description="Nome do médico solicitante ou responsável")
    crm: Optional[str] = Field(default=None, description="Registro CRM com UF (ex.: 145892-SP)")


class DadosExtraidos(_CompatBaseModel):
    """Entidades clínicas estruturadas extraídas pelo motor LLM multimodal."""

    paciente: DadosPaciente
    medico_solicitante: DadosMedicoSolicitante
    exame_realizado: Optional[str] = Field(
        default=None,
        description="Exame realizado/solicitado ou prescrição medicamentosa principal",
    )
    diagnostico_principal: Optional[str] = Field(
        default=None,
        description="Hipótese diagnóstica ou conclusão clínica principal",
    )
    cid_sugerido: Optional[str] = Field(
        default=None,
        description="Código CID-10 sugerido (ex.: I26.9 para Tromboembolismo Pulmonar Agudo)",
    )
    medicamentos_prescritos: Optional[list[str]] = Field(
        default=None,
        description="Lista de medicamentos e posologias quando aplicável",
    )


class NotificacaoGerada(_CompatBaseModel):
    canal: str = Field(..., description="Canal de destino do alerta (ex.: Alerta_Plantao_Medico, Painel_Auditoria_HitL)")
    mensagem: str = Field(..., description="Mensagem estruturada enviada para a equipe responsável")


class DecisaoRoteamento(_CompatBaseModel):
    """Resultado do grafo de decisão condicional do agente MediFlow."""

    destino_principal: DestinoRoteamentoEnum
    requer_auditoria_humana: bool = Field(
        ...,
        description="True quando o score de confiança < 0.85 ou há dados ilegíveis/conflitantes",
    )
    justificativa_roteamento: str = Field(
        ...,
        description="Explicação clínica e técnica para a decisão de roteamento",
    )
    notificacao_gerada: Optional[NotificacaoGerada] = None


class ArmazenamentoOCI(_CompatBaseModel):
    """Registro de persistência e segregação no OCI Object Storage (Camada Always Free)."""

    bucket: str = Field(default="mediflow-documentos-clinicos")
    caminho_objeto: str = Field(
        ...,
        description="Caminho segregado no bucket (ex.: processados/urgentes/DOC-CLIN-2026-8942.json)",
    )
    status_backup: str = Field(
        default="sucesso",
        description="Status da persistência (sucesso | fallback_local_always_free)",
    )


class ResultadoTriagemOutput(_CompatBaseModel):
    """Contrato oficial de saída estruturada do MediFlow conforme especificação medflow.md."""

    status: str = Field(default="processado", description="processado | retido_auditoria_humana")
    documento_id: str
    classificacao: ClassificacaoDocumento
    dados_extraidos: DadosExtraidos
    decisao_roteamento: DecisaoRoteamento
    armazenamento_oci: ArmazenamentoOCI