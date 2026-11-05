"""
MediFlow — Testes do Componente Visual do Alerta de Plantão (Release 1.3, CARD-06)
Hackathon ONE G10 — Oracle Next Education & Alura (Equipo 22)

Só o HTML: o Streamlit não é importado.

Execução:
  pytest week3/test_ui_alertas.py -v
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from week3.ui_alertas import descrever_entrega, html_alerta_plantao, linhas_historico, texto_reenvio


def test_conteudo_do_documento_e_escapado():
    saida = html_alerta_plantao("DOC<1>", "<script>alert(1)</script>", "sucesso")
    assert "<script>" not in saida
    assert "&lt;script&gt;" in saida
    assert "DOC&lt;1&gt;" in saida


def test_alerta_e_anunciado_para_leitor_de_tela_e_respeita_movimento_reduzido():
    saida = html_alerta_plantao("DOC-1", "TEP", "sucesso")
    assert 'role="alert"' in saida
    assert "prefers-reduced-motion" in saida


def test_entrega_mostra_simulado_e_falha_sem_disfarce():
    assert descrever_entrega("sucesso")[0] == "entregue ao plantão"
    assert "simulado" in descrever_entrega("sucesso_mock")[0]
    assert descrever_entrega("erro_http_500") == ("falhou (erro_http_500)", "falha")
    assert descrever_entrega(None) == ("sem registro de envio", "falha")


def test_urgencia_com_revisao_avisa_as_duas_coisas():
    saida = html_alerta_plantao("DOC-1", None, "sucesso", tambem_em_revisao=True)
    assert "Quadro crítico agudo" in saida
    assert "revisão humana" in saida


def test_historico_mostra_o_mais_recente_primeiro():
    alertas = [
        {"timestamp": "2026-11-05T10:00:00.123", "documento_id": "DOC-A", "canal": "Plantao", "status": "sucesso",
         "latencia_ms": 120.5, "tentativas": 1, "reenvios": 0, "alerta_id": "a1"},
        {"timestamp": "2026-11-05T10:05:00.456", "documento_id": "DOC-B", "canal": "Plantao", "status": "erro_http_503",
         "latencia_ms": 900.0, "tentativas": 2, "reenvios": 1, "alerta_id": "b2"},
    ]
    linhas = linhas_historico(alertas)
    assert [l["Documento"] for l in linhas] == ["DOC-B", "DOC-A"]
    assert linhas[0]["Horário"] == "2026-11-05 10:05:00"
    assert linhas[0]["Entrega"].startswith("falhou")
    assert linhas[0]["Reenvios"] == 1


def test_aviso_de_reenvio_diz_o_que_aconteceu():
    assert texto_reenvio({"status_envio": "sucesso", "alerta_id": "a1", "latencia_ms": 80})[0] == "success"
    assert texto_reenvio({"status_envio": "ja_entregue", "alerta_id": "a1"})[0] == "warning"
    assert "WEBHOOK_EMERGENCY_URL" in texto_reenvio({"status_envio": "sem_webhook", "alerta_id": "a1"})[1]
    nivel, texto = texto_reenvio({"status_envio": "falha_conexao", "alerta_id": "a1", "detalhes": "recusada"})
    assert nivel == "error" and "recusada" in texto

