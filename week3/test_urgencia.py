"""
MediFlow — Testes de Regressão: Urgência com Dado Faltando (Release 1.3)
Hackathon ONE G10 — Oracle Next Education & Alura (Equipo 22)

Um achado crítico com dado faltando (nome do paciente, CRM borrado) caía na fila de revisão humana
sem disparar o alerta do plantão: o score penalizado era checado antes da urgência. Casos
equivalentes no conjunto sintético: SINT-025 (TEP sem o nome do paciente).

Execução:
  pytest week3/test_urgencia.py -v
"""

import sys
import tempfile
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from mediflow_schemas import (
    ClassificacaoDocumento,
    DestinoRoteamentoEnum,
    DocumentoClinicoInput,
    NivelPrioridadeEnum,
    TipoArquivoEnum,
)
from week3.agent import MediFlowStateGraphAgent
from week3.notifications import NotificationDispatcher
from week3.storage import OCIStorageServiceV3

TEP_SEM_NOME = DocumentoClinicoInput(
    documento_id="DOC-REG-TEP-SEM-NOME",
    tipo_arquivo=TipoArquivoEnum.PDF,
    documento_texto=(
        "HOSPITAL SANTA LUCIA - LAUDO DE EXAME RADIOLOGICO. "
        "Solicitante: Dra. Renata Silveira CRM-SP 145892. Exame: Tomografia de Torax com contraste. "
        "Achados: Falha de enchimento em arteria pulmonar principal direita. "
        "CONCLUSÃO: Quadro compativel com Tromboembolismo Pulmonar Agudo."
    ),
    canal_origem="Pronto_Socorro",
)

TEP_CRM_BORRADO = DocumentoClinicoInput(
    documento_id="DOC-REG-TEP-CRM-BORRADO",
    tipo_arquivo=TipoArquivoEnum.IMAGEM,
    documento_texto=(
        "LAUDO DE EXAME RADIOLOGICO. Paciente: Carlos Eduardo Mendes, 52 anos. "
        "Solicitante: Dra. Renata Silveira CRM borrado. Exame: Angiotomografia de Torax. "
        "CONCLUSÃO: Quadro compativel com Tromboembolismo Pulmonar Agudo."
    ),
    canal_origem="Pronto_Socorro",
)


@pytest.fixture
def temp_workspace(monkeypatch):
    """Ambiente temporário isolado, como em test_week3.py, sempre no fallback heurístico."""
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = OCIStorageServiceV3(
            bucket_name="mediflow-test-bucket",
            local_fallback_dir=Path(tmpdir) / "oci_bucket",
            db_path=Path(tmpdir) / "test_audit.db",
        )
        dispatcher = NotificationDispatcher(mock_mode=True)
        agent = MediFlowStateGraphAgent(storage_service=storage, notification_dispatcher=dispatcher)
        yield {"agent": agent, "dispatcher": dispatcher}


@pytest.mark.parametrize("documento", [TEP_SEM_NOME, TEP_CRM_BORRADO], ids=["sem_nome", "crm_borrado"])
def test_urgencia_com_dado_faltando_avisa_plantao_e_vai_a_revisao(temp_workspace, documento):
    resultado = temp_workspace["agent"].run(documento)

    # A urgência sobrevive à penalidade do validador
    assert resultado.classificacao.nivel_prioridade == NivelPrioridadeEnum.URGENTE
    assert resultado.classificacao.score_confianca_classificacao < 0.85

    # O plantão é avisado...
    assert resultado.decisao_roteamento.destino_principal == DestinoRoteamentoEnum.FILA_EMERGENCIA_MEDICA
    assert resultado.decisao_roteamento.notificacao_gerada.canal == "Alerta_Plantao_Medico"
    alertas = temp_workspace["dispatcher"].historico_alertas
    assert [a.documento_id for a in alertas] == [documento.documento_id]

    # ...e o documento também entra na revisão humana, sem ficar "retido"
    assert resultado.decisao_roteamento.requer_auditoria_humana is True
    assert "Auditoria Humana" in resultado.decisao_roteamento.justificativa_roteamento
    assert resultado.status == "processado"
    assert resultado.armazenamento_oci.caminho_objeto.startswith("auditoria_humana/")


@pytest.mark.parametrize(
    "prioridade, score, rota",
    [
        (NivelPrioridadeEnum.URGENTE, 0.40, "emergency_route"),
        (NivelPrioridadeEnum.URGENTE, 0.99, "emergency_route"),
        (NivelPrioridadeEnum.ROTINA, 0.40, "hitl_route"),
        (NivelPrioridadeEnum.REVISAO_HUMANA, 0.90, "hitl_route"),
        (NivelPrioridadeEnum.ROTINA, 0.90, "routine_route"),
    ],
)
def test_decide_route_urgencia_antes_do_score(prioridade, score, rota):
    classificacao = ClassificacaoDocumento(
        tipo_documento="Laudo de Exame de Imagem",
        especialidade="Radiologia / Pneumologia",
        nivel_prioridade=prioridade,
        score_confianca_classificacao=score,
    )
    assert MediFlowStateGraphAgent.decide_route({"classificacao": classificacao}) == rota
