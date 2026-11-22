"""
MediFlow — Testes End-to-End FastAPI, Histórico por CRM e Contratos TISS/TUSS
Hackathon ONE G10 — Oracle Next Education & Alura (Equipo 22)
Sprint M4: CARD-22 (#31), CARD-23 (#32), CARD-24 (#33)
"""

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app import api
from mediflow_schemas import GuiaAutorizacaoTISS


@pytest.fixture
def client():
    return TestClient(api)


# =============================================================================
# CARD-23 (#32) — Conformidade Pydantic v2 com Padrões ANS TISS / TUSS
# =============================================================================

def test_guia_tiss_valida():
    """Valida construção correta de Guia de Autorização TISS com conformidade ANS."""
    guia = GuiaAutorizacaoTISS(
        numero_guia_prestador="GUIA-2026-9901",
        registro_ans="345678",  # 6 dígitos
        numero_carteira_beneficiario="001299887766001",
        nome_beneficiario="Roberto Carlos Silva",
        codigo_tuss_procedimento="40808033",  # 8 dígitos
        descricao_procedimento="Ressonância Magnética de Crânio",
        carater_atendimento="Eletivo",
        cid10_principal="G43.0",
        crm_solicitante="CRM-SP 98765",
    )
    assert guia.registro_ans == "345678"
    assert guia.codigo_tuss_procedimento == "40808033"
    assert guia.carater_atendimento == "Eletivo"


def test_guia_tiss_registro_ans_invalido():
    """Valida rejeição de Registro ANS fora do padrão numérico de 6 dígitos."""
    with pytest.raises(ValidationError) as exc:
        GuiaAutorizacaoTISS(
            numero_guia_prestador="GUIA-ERR-001",
            registro_ans="1234",  # Apenas 4 dígitos
            numero_carteira_beneficiario="0012",
            nome_beneficiario="Teste",
            codigo_tuss_procedimento="40808033",
            descricao_procedimento="Exame",
            crm_solicitante="CRM-SP 123",
        )
    assert "Registro ANS inválido" in str(exc.value)


def test_guia_tiss_codigo_tuss_invalido():
    """Valida rejeição de Código TUSS que não contenha 8 dígitos numéricos."""
    with pytest.raises(ValidationError) as exc:
        GuiaAutorizacaoTISS(
            numero_guia_prestador="GUIA-ERR-002",
            registro_ans="123456",
            numero_carteira_beneficiario="0012",
            nome_beneficiario="Teste",
            codigo_tuss_procedimento="999",  # Inválido
            descricao_procedimento="Procedimento",
            crm_solicitante="CRM-SP 123",
        )
    assert "Código TUSS inválido" in str(exc.value)


# =============================================================================
# CARD-22 (#31) & CARD-24 (#33) — Endpoints de Busca Histórica e Testes E2E
# =============================================================================

def test_e2e_triagem_e_busca_documento(client):
    """Executa triagem via POST e busca subsequente pelo ID do documento."""
    payload = {
        "documento_id": "DOC-E2E-M4-001",
        "tipo_arquivo": "PDF",
        "documento_texto": "HOSPITAL SANTA LUCIA - RECEITUARIO MEDICO\nPaciente: Juliana Paes\nDr. Marcelo Dantas CRM: 443322-RJ\nPrescricao: Amoxicilina 500mg 8/8h por 7 dias.",
        "canal_origem": "Ambulatorio",
    }
    resp_triagem = client.post("/api/v1/triagem", json=payload)
    assert resp_triagem.status_code == 200
    dados_triagem = resp_triagem.json()
    assert dados_triagem["documento_id"] == "DOC-E2E-M4-001"

    # Busca detalhada por ID
    resp_doc = client.get("/api/v1/documentos/DOC-E2E-M4-001")
    assert resp_doc.status_code == 200
    dados_doc = resp_doc.json()
    assert dados_doc["documento_id"] == "DOC-E2E-M4-001"
    assert dados_doc["status"] in ("encontrado", "em_auditoria")


def test_e2e_busca_documento_inexistente_retorna_404(client):
    """Valida retorno HTTP 404 para documento inexistente."""
    resp = client.get("/api/v1/documentos/DOC-NAO-EXISTE-9999")
    assert resp.status_code == 404
    assert "não encontrado" in resp.json()["detail"]


def test_e2e_historico_com_filtros_crm_e_prioridade(client):
    """Testa listagem paginada e filtros dinâmicos na rota /api/v1/historico."""
    from mediflow_agent import SCENARIO_2_URGENCY_TEP

    # Insere caso urgente oficial
    payload_urgente = {
        "documento_id": "DOC-E2E-M4-URG",
        "tipo_arquivo": "PDF",
        "documento_texto": SCENARIO_2_URGENCY_TEP.documento_texto,
        "canal_origem": "Pronto_Socorro",
    }
    client.post("/api/v1/triagem", json=payload_urgente)

    # Consulta sem filtro
    resp_hist = client.get("/api/v1/historico?page=1&limit=10")
    assert resp_hist.status_code == 200
    dados_hist = resp_hist.json()
    assert dados_hist["total"] >= 1
    assert "documentos" in dados_hist

    # Filtro por prioridade Urgente
    resp_urg = client.get("/api/v1/historico?prioridade=Urgente")
    assert resp_urg.status_code == 200
    dados_urg = resp_urg.json()
    assert any(d["documento_id"] == "DOC-E2E-M4-URG" for d in dados_urg["documentos"])
