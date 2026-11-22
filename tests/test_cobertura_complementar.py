"""
MediFlow — Testes Complementares de Cobertura de Código para atingir >= 90% (CARD-37 / #46)
Hackathon ONE G10 — Oracle Next Education & Alura (Equipo 22)
Persona: Arquiteto Carlos Vance (Carlos Magno — Tech Lead & SRE/IA)
"""

import json
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from app import api, _audit_queue
from mediflow_agent import (
    MediFlowAgentGraph,
    SCENARIO_1_ROUTINE,
    SCENARIO_2_URGENCY_TEP,
    SCENARIO_3_AMBIGUOUS_HITL,
)
from mediflow_schemas import DocumentoClinicoInput, TipoArquivoEnum, ResultadoTriagemOutput
from oci_storage import OCIStorageService, OCIATPManager
from week5.exportacao import main as exportacao_main
from week5.auditoria_orcamento_oci import gerar_relatorio_texto


@pytest.fixture
def client():
    return TestClient(api)


# =============================================================================
# Cobertura complementar: app.py rotas FastAPI adicionais
# =============================================================================

def test_app_root_redirect(client):
    """Testa redirecionamento da raiz / para /docs."""
    resp = client.get("/", follow_redirects=False)
    assert resp.status_code in (302, 307)
    assert resp.headers["location"] == "/docs"


def test_app_aprovar_hitl_fluxo_completo(client):
    """Testa aprovação de documento na fila de revisão humana."""
    doc_id = "DOC-HITL-APROV-001"
    resultado_mock = ResultadoTriagemOutput(
        status="retido_auditoria_humana",
        documento_id=doc_id,
        classificacao={
            "tipo_documento": "Receituário",
            "especialidade": "Clínica Médica",
            "nivel_prioridade": "Revisao_Humana",
            "score_confianca_classificacao": 0.70,
        },
        dados_extraidos={
            "paciente": {"nome": "Paciente Teste"},
            "medico_solicitante": {"crm": None},
        },
        decisao_roteamento={
            "destino_principal": "Fila_Revisao_Humana",
            "requer_auditoria_humana": True,
            "justificativa_roteamento": "Sem CRM",
        },
        armazenamento_oci={"caminho_objeto": "auditoria_humana/DOC-HITL-APROV-001.json"},
    )
    _audit_queue[doc_id] = resultado_mock

    # Consulta fila
    resp_lista = client.get("/api/v1/auditoria")
    assert resp_lista.status_code == 200

    # Aprova com CRM corrigido
    resp_aprov = client.post(f"/api/v1/auditoria/{doc_id}/aprovar?crm_corrigido=CRM-SP 998811")
    assert resp_aprov.status_code == 200
    assert "aprovado pelo auditor" in resp_aprov.json()["mensagem"]
    assert doc_id not in _audit_queue

    # Tentativa de aprovar novamente -> 404
    resp_404 = client.post(f"/api/v1/auditoria/{doc_id}/aprovar?crm_corrigido=CRM-SP 998811")
    assert resp_404.status_code == 404


def test_app_historico_filtros_multiplos(client):
    """Testa filtros combinados na rota de histórico."""
    resp = client.get("/api/v1/historico?crm=CRM-SP 12345&tipo_documento=Receituário Médico&page=1&limit=5")
    assert resp.status_code == 200
    assert "documentos" in resp.json()


# =============================================================================
# Cobertura complementar: mediflow_agent.py nós, fallback e mock NIM
# =============================================================================

def test_mediflow_agent_mock_nim_chamada():
    """Testa execução do grafo com chamada simulada à API NVIDIA NIM."""
    agent = MediFlowAgentGraph()
    agent.nvidia_api_key = "nvapi-fake-test-key"

    fake_response_content = json.dumps({
        "tipo_documento": "Laudo de Tomografia",
        "especialidade": "Pneumologia",
        "nivel_prioridade": "Urgente",
        "score_confianca": 0.99,
        "paciente": {"nome": "Teste NIM", "idade": 50},
        "medico_solicitante": {"nome": "Dr. Silveira", "crm": "12345-SP"},
        "diagnostico_principal": "Tromboembolismo Pulmonar",
        "cid_sugerido": "I26.9",
        "destino_principal": "Fila_Emergencia_Medica",
        "justificativa_roteamento": "Achado crítico",
    })

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": fake_response_content}}]
    }

    doc_entrada = DocumentoClinicoInput(
        documento_id="DOC-NIM-TEST-001",
        tipo_arquivo=TipoArquivoEnum.IMAGEM,
        documento_texto="Laudo escaneado",
        arquivo_binario_b64="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==",
        canal_origem="Pronto_Socorro",
    )

    with patch("httpx.Client.post", return_value=mock_resp):
        res = agent.run(doc_entrada)
        assert res.documento_id == "DOC-NIM-TEST-001"
        assert res.classificacao.nivel_prioridade.value == "Urgente"
        assert res.dados_extraidos.paciente.nome == "Teste NIM"


def test_mediflow_agent_fallback_em_erro_nim():
    """Valida acionamento resiliente do fallback heurístico quando a API externa retorna erro 500."""
    agent = MediFlowAgentGraph()
    agent.nvidia_api_key = "nvapi-fake-test-key"

    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_resp.text = "Internal Server Error"

    doc_entrada = DocumentoClinicoInput(
        documento_id="DOC-NIM-ERR-001",
        tipo_arquivo=TipoArquivoEnum.PDF,
        documento_texto="HOSPITAL SANTA LUCIA - RECEITUARIO MEDICO\nPaciente: Carlos\nDr. Renato CRM: 123-SP",
        arquivo_binario_b64="fake_pdf_binary_b64",
        canal_origem="Ambulatorio",
    )

    with patch("httpx.Client.post", return_value=mock_resp):
        res = agent.run(doc_entrada)
        assert res.documento_id == "DOC-NIM-ERR-001"
        assert res.classificacao.score_confianca_classificacao > 0


# =============================================================================
# Cobertura complementar: oci_storage.py e exportacao CLI
# =============================================================================

def test_oci_storage_resolucao_caminhos():
    """Testa resolve_object_path para todos os ramos condicionais."""
    assert OCIStorageService.resolve_object_path("DOC-1", False, "Rotina", is_raw_ingestion=True) == "recebidos/DOC-1.json"
    assert OCIStorageService.resolve_object_path("DOC-2", True, "Rotina") == "auditoria_humana/DOC-2.json"
    assert OCIStorageService.resolve_object_path("DOC-3", False, "Urgente") == "processados/urgentes/DOC-3.json"
    assert OCIStorageService.resolve_object_path("DOC-4", False, "Rotina") == "processados/rotina/DOC-4.json"


def test_exportacao_cli_execucao(tmp_path, monkeypatch):
    """Testa interface CLI do script de exportação de prontuários."""
    csv_file = tmp_path / "cli_export.csv"
    test_args = ["exportacao.py", "--formato", "csv", "--saida", str(csv_file)]
    monkeypatch.setattr("sys.argv", test_args)
    exportacao_main()
    assert csv_file.exists()


def test_gerar_relatorio_texto_standalone(tmp_path):
    """Testa geração do relatório FinOps em arquivo temporário."""
    p = tmp_path / "finops_audit.txt"
    txt = gerar_relatorio_texto(output_file=str(p))
    assert "FINOPS OCI" in txt
    assert p.exists()
