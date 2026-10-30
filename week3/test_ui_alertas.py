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

from week3.ui_alertas import descrever_entrega, html_alerta_plantao


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
