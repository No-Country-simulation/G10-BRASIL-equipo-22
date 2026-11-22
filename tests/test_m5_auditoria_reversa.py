"""
MediFlow — Testes de Auditoria Reversa, Swagger v1.5.0 e Homologação UAT
Hackathon ONE G10 — Oracle Next Education & Alura (Equipo 22)
Sprint M5: CARD-34 (#43), CARD-35 (#44), CARD-36 (#45)
"""

import pytest
from fastapi.testclient import TestClient

from app import api
from oci_storage import OCIATPManager
from week5.uat_20_laudos import executar_bateria_uat


@pytest.fixture
def client():
    return TestClient(api)


# =============================================================================
# CARD-34 (#43) — Módulo de Auditoria Reversa (Reabertura de Laudos Aprovados)
# =============================================================================

def test_reabrir_laudo_aprovado_sucesso(client):
    """Testa reabertura de laudo previamente liberado para auditoria reversa."""
    atp = OCIATPManager()
    doc_id = "DOC-REABRIR-001"
    atp.salvar_registro(
        documento_id=doc_id,
        tipo_documento="Receituário Médico",
        crm_medico="CRM-SP 12345",
        paciente_nome="Marcos Valério",
        prioridade="Rotina",
        score_confianca=0.98,
        requer_auditoria=False,
        payload_json={
            "documento_id": doc_id,
            "status": "processado",
            "classificacao": {
                "tipo_documento": "Receituário Médico",
                "especialidade": "Clínica Médica",
                "nivel_prioridade": "Rotina",
                "score_confianca_classificacao": 0.98,
            },
            "dados_extraidos": {
                "paciente": {"nome": "Marcos Valério"},
                "medico_solicitante": {"crm": "CRM-SP 12345"},
            },
            "decisao_roteamento": {
                "destino_principal": "Farmacia_Hospitalar",
                "requer_auditoria_humana": False,
                "justificativa_roteamento": "Aprovado automaticamente",
            },
            "armazenamento_oci": {"caminho_objeto": "processados/rotina/DOC-REABRIR-001.json"},
        },
    )

    # Supervisor médico solicita reabertura
    payload_reabertura = {
        "motivo_reabertura": "Dosagem informada de medicamento pode estar acima do recomendado para a idade",
        "supervisor_crm": "CRM-SP 99887",
    }
    resp = client.post(f"/api/v1/auditoria/{doc_id}/reabrir", json=payload_reabertura)
    assert resp.status_code == 200
    dados = resp.json()
    assert dados["novo_status"] == "em_auditoria_reversa"
    assert dados["supervisor_crm"] == "CRM-SP 99887"
    assert "reaberto com sucesso" in dados["mensagem"]

    # Verifica se documento reapareceu na fila de auditoria
    resp_auditoria = client.get("/api/v1/auditoria")
    assert resp_auditoria.status_code == 200
    fila = resp_auditoria.json()
    assert any(item["documento_id"] == doc_id for item in fila)


def test_reabrir_laudo_inexistente_retorna_404(client):
    """Testa rejeição de reabertura para documento inexistente."""
    payload = {
        "motivo_reabertura": "Auditoria de rotina",
        "supervisor_crm": "CRM-SP 11111",
    }
    resp = client.post("/api/v1/auditoria/DOC-INEXISTENTE-9999/reabrir", json=payload)
    assert resp.status_code == 404
    assert "não encontrado" in resp.json()["detail"]


# =============================================================================
# CARD-36 (#45) — Documentação OpenAPI / Swagger v1.5.0
# =============================================================================

def test_swagger_openapi_v15_metadata(client):
    """Valida especificações e schemas OpenAPI para avaliação da banca examinadora."""
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    openapi = resp.json()

    assert openapi["info"]["version"] == "1.5.0"
    assert "MediFlow" in openapi["info"]["title"]
    assert "tags" in openapi
    nomes_tags = [t["name"] for t in openapi["tags"]]
    assert "Triagem & IA" in nomes_tags
    assert "Auditoria & HitL" in nomes_tags
    assert "Histórico & Consultas" in nomes_tags
    assert "SRE & Confiabilidade" in nomes_tags


# =============================================================================
# CARD-35 (#44) — Homologação UAT
# =============================================================================

def test_uat_execucao_amostra():
    """Valida execução da bateria UAT com documentos sintéticos."""
    resultado = executar_bateria_uat(limite=3)
    assert resultado["total_documentos"] == 3
    assert resultado["latencia_media_ms"] < 3000.0  # SLA < 3s
    assert len(resultado["resultados"]) == 3
