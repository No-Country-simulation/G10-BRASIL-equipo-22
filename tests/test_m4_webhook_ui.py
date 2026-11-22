"""
MediFlow — Testes de Ingestão com Token Caching, Webhooks Enriquecidos e UI de Status
Hackathon ONE G10 — Oracle Next Education & Alura (Equipo 22)
Sprint M4: CARD-16 (#25), CARD-17 (#26), CARD-18 (#27)
"""

import io
from pathlib import Path
import pytest
import pypdfium2 as pdfium

import mediflow_ingestao as ing
from week3.notifications import (
    NotificationDispatcher,
    DADOS_HOSPITALARES_PADRAO,
    formatar_slack_blocks,
    formatar_discord_embeds,
    formatar_erp_clinico_hl7,
)
from week3.ui_alertas import (
    calcular_metricas_alertas,
    linhas_historico,
    descrever_entrega,
    texto_reenvio,
)


def _criar_pdf_sintetico(texto: str = "LAUDO MEDICO DE TESTE CLINICO") -> bytes:
    doc = pdfium.PdfDocument.new()
    font = doc.get_font("Helvetica")
    page = doc.new_page(width=595, height=842)
    text_obj = pdfium.PdfTextObject.new(font=font, font_size=16)
    text_obj.set_text(texto)
    text_obj.set_matrix((1, 0, 0, 1, 50, 750))
    page.gen_page_content()
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


# =============================================================================
# CARD-16 (#25) — Ingestão Multimodal com Token Caching e Conversor PDF
# =============================================================================

def test_converter_pdf_para_imagens_base64():
    """Valida conversão de páginas de PDF para Base64."""
    # Usar um documento sintético existente
    pdf_path = Path("dados_sinteticos/documentos/SINT-013.pdf")
    if pdf_path.exists():
        dados = pdf_path.read_bytes()
    else:
        dados = _criar_pdf_sintetico()

    imagens = ing.converter_pdf_para_imagens_base64(dados)
    assert isinstance(imagens, list)


def test_token_caching_pdf_reprocessamento():
    """Verifica que o segundo processamento do mesmo PDF utiliza cache de tokens."""
    ing.limpar_cache_tokens_pdf()
    pdf_path = Path("dados_sinteticos/documentos/SINT-013.pdf")
    dados = pdf_path.read_bytes() if pdf_path.exists() else _criar_pdf_sintetico()

    # Primeiro acesso -> Cache Miss
    doc1 = ing.ingerir(dados)
    assert doc1.cache_hit is False
    assert doc1.tokens_estimados > 0
    assert doc1.tokens_economizados == 0

    # Segundo acesso -> Cache Hit
    doc2 = ing.ingerir(dados)
    assert doc2.cache_hit is True
    assert doc2.tokens_economizados == doc1.tokens_estimados
    assert doc2.tokens_estimados == doc1.tokens_estimados


def test_limpar_cache_tokens_pdf():
    """Confirma esvaziamento do cache de páginas de PDF."""
    pdf_path = Path("dados_sinteticos/documentos/SINT-013.pdf")
    dados = pdf_path.read_bytes() if pdf_path.exists() else _criar_pdf_sintetico()

    ing.ingerir(dados)
    assert len(ing._CACHE_PAGINAS_PDF) > 0
    ing.limpar_cache_tokens_pdf()
    assert len(ing._CACHE_PAGINAS_PDF) == 0


# =============================================================================
# CARD-17 (#26) — Templates de Webhook com Link Seguro e Dados Hospitalares
# =============================================================================

def test_webhook_payload_enriquecido():
    """Verifica enriquecimento de payload de emergência com cards e link seguro."""
    dispatcher = NotificationDispatcher(mock_mode=True)
    resp = dispatcher.dispatch_emergency_alert(
        documento_id="DOC-CARD17-001",
        paciente_nome="Maria de Lurdes",
        diagnostico="Tromboembolismo Pulmonar Agudo (TEP)",
        crm_solicitante="CRM-SP 98765",
    )

    payload = resp["payload"]
    assert "link_seguro" in payload
    assert "token=" in payload["link_seguro"]
    assert "dados_hospitalares" in payload
    assert payload["dados_hospitalares"]["unidade"] == DADOS_HOSPITALARES_PADRAO["unidade"]

    # Valida blocos para Slack Block Kit
    assert "slack_blocks" in payload
    assert any(b.get("type") == "header" for b in payload["slack_blocks"])
    assert any(b.get("type") == "actions" for b in payload["slack_blocks"])

    # Valida cards para Discord
    assert "discord_embeds" in payload
    embed = payload["discord_embeds"][0]
    assert embed["color"] == 16711680
    assert "Maria de Lurdes" in str(embed["fields"])

    # Valida interoperabilidade ERP clínico (FHIR / HL7)
    assert "erp_clinico_payload" in payload
    erp = payload["erp_clinico_payload"]
    assert erp["resourceType"] == "CommunicationRequest"
    assert erp["priority"] == "stat"


def test_webhook_dados_hospitalares_customizados():
    """Confirma que dados hospitalares customizados são respeitados."""
    dispatcher = NotificationDispatcher(mock_mode=True)
    custom_hosp = {
        "unidade": "Hospital São Lucas - Emergência Cardiológica",
        "cnpj": "99.888.777/0001-66",
        "setor_plantao": "Hemodinâmica",
        "ramal_urgencia": "5005",
        "telefone_plantao": "+55 21 2222-3333",
    }
    resp = dispatcher.dispatch_emergency_alert(
        documento_id="DOC-CARD17-002",
        paciente_nome="João Silva",
        diagnostico="Infarto Agudo do Miocárdio (IAM)",
        crm_solicitante="CRM-RJ 12345",
        dados_hospitalares=custom_hosp,
    )
    assert resp["payload"]["dados_hospitalares"]["unidade"] == "Hospital São Lucas - Emergência Cardiológica"
    assert "5005" in resp["payload"]["mensagem"]


# =============================================================================
# CARD-18 (#27) — Visualizador de Status de Entrega e Métricas SRE
# =============================================================================

def test_calcular_metricas_alertas():
    """Valida métricas executivas de entrega de webhooks."""
    alertas = [
        {"status": "sucesso", "latencia_ms": 120.0},
        {"status": "sucesso", "latencia_ms": 80.0},
        {"status": "sucesso_mock", "latencia_ms": 0.0},
        {"status": "falha_conexao", "latencia_ms": 3000.0},
    ]
    metricas = calcular_metricas_alertas(alertas)
    assert metricas["total"] == 4
    assert metricas["entregues"] == 2
    assert metricas["simulados"] == 1
    assert metricas["falhas"] == 1
    assert metricas["taxa_sucesso_pct"] == 75.0
    assert metricas["latencia_media_ms"] == 800.0  # (120 + 80 + 0 + 3000) / 4 = 800.0


def test_linhas_historico_formatacao():
    """Garante formatação adequada das linhas da tabela Streamlit."""
    alertas = [
        {
            "timestamp": "2026-11-22T10:30:00.123456",
            "documento_id": "DOC-99",
            "canal": "UTI",
            "status": "sucesso",
            "latencia_ms": 45.2,
            "tentativas": 1,
            "alerta_id": "a1b2c3d4",
        }
    ]
    linhas = linhas_historico(alertas)
    assert len(linhas) == 1
    assert linhas[0]["Documento"] == "DOC-99"
    assert linhas[0]["Entrega"] == "entregue ao plantão"
    assert linhas[0]["ID"] == "a1b2c3d4"
