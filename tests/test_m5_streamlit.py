"""
MediFlow — Testes de Design System Clínico Manchester, Visualizador e Filtros HitL
Hackathon ONE G10 — Oracle Next Education & Alura (Equipo 22)
Sprint M5: CARD-28 (#37), CARD-29 (#38), CARD-30 (#39), Macro #8
"""

import pytest

from week5_ui_helpers import (
    CORES_MANCHESTER,
    filtrar_fila_auditoria,
    gerar_audio_alerta_sintetico,
    gerar_badge_manchester,
)


# =============================================================================
# CARD-29 (#38) — Design System Clínico com Cores Manchester e Beep Sintético
# =============================================================================

def test_gerar_badge_manchester_urgente():
    """Valida badge vermelho Manchester para casos de emergência médica."""
    badge = gerar_badge_manchester("Urgente")
    assert "background-color: #b71c1c" in badge
    assert "Emergência" in badge
    assert "mf-badge" in badge


def test_gerar_badge_manchester_revisao_humana():
    """Valida badge de atenção para casos retidos pelo score ou ambiguidade."""
    badge = gerar_badge_manchester("Revisao_Humana")
    assert "background-color: #e65100" in badge
    assert "Retido HitL" in badge


def test_gerar_audio_alerta_sintetico():
    """Valida tag de áudio sintetizada em Base64 para notificação sonora."""
    audio_tag = gerar_audio_alerta_sintetico()
    assert "<audio autoplay" in audio_tag
    assert "data:audio/wav;base64," in audio_tag


# =============================================================================
# CARD-30 (#39) — Filtros Dinâmicos na Fila de Auditoria (HitL)
# =============================================================================

@pytest.fixture
def fila_exemplo():
    return [
        {
            "documento_id": "DOC-001",
            "especialidade": "Radiologia / Pneumologia",
            "prioridade": "Urgente",
            "paciente": "Carlos Mendes",
            "crm": "12345-SP",
        },
        {
            "documento_id": "DOC-002",
            "especialidade": "Cardiologia",
            "prioridade": "Alta",
            "paciente": "Beatriz Souza",
            "crm": "99887-RJ",
        },
        {
            "documento_id": "DOC-003",
            "especialidade": "Clínica Médica",
            "prioridade": "Revisao_Humana",
            "paciente": "João Pedro",
            "crm": "Sem CRM",
        },
    ]


def test_filtrar_por_especialidade(fila_exemplo):
    """Testa filtro dinâmico por especialidade médica."""
    res = filtrar_fila_auditoria(fila_exemplo, especialidade="Cardiologia")
    assert len(res) == 1
    assert res[0]["documento_id"] == "DOC-002"


def test_filtrar_por_prioridade(fila_exemplo):
    """Testa priorização imediata de casos Urgentes pelo auditor."""
    res = filtrar_fila_auditoria(fila_exemplo, prioridade="Urgente")
    assert len(res) == 1
    assert res[0]["documento_id"] == "DOC-001"


def test_filtrar_busca_textual(fila_exemplo):
    """Testa busca rápida por nome de paciente ou CRM."""
    res = filtrar_fila_auditoria(fila_exemplo, busca="Beatriz")
    assert len(res) == 1
    assert res[0]["paciente"] == "Beatriz Souza"


def test_filtro_todas_retorna_completo(fila_exemplo):
    """Garante que seleção 'Todas' não restringe os resultados."""
    res = filtrar_fila_auditoria(fila_exemplo, especialidade="Todas", prioridade="Todas")
    assert len(res) == 3
