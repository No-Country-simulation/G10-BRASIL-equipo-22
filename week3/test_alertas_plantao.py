"""
MediFlow — Testes do Despachador de Alertas de Plantão (Release 1.3, CARD-04)
Hackathon ONE G10 — Oracle Next Education & Alura (Equipo 22)

Entrega real com nova tentativa em erro transitório, falha que fica marcada no histórico e
modo simulado que avisa em vez de fingir entrega. O cliente HTTP é falso: nada sai da máquina.

Execução:
  pytest week3/test_alertas_plantao.py -v
"""

import logging
import sys
from pathlib import Path

import httpx
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import week3.notifications as notifications
from week3.notifications import NotificationDispatcher

URL = "https://webhook.exemplo.invalid/plantao"


class _Resposta:
    def __init__(self, status_code):
        self.status_code = status_code
        self.is_success = 200 <= status_code < 300
        self.text = "ok" if self.is_success else f"erro {status_code}"


@pytest.fixture
def servidor(monkeypatch):
    """Troca o httpx.Client por um falso que responde em sequência (status ou exceção)."""
    estado = {"respostas": [], "chamadas": 0}

    class ClienteFalso:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def post(self, url, **kwargs):
            estado["chamadas"] += 1
            resposta = estado["respostas"].pop(0)
            if isinstance(resposta, Exception):
                raise resposta
            return _Resposta(resposta)

    monkeypatch.setattr(notifications.httpx, "Client", ClienteFalso)
    return estado


def disparar(dispatcher):
    return dispatcher.dispatch_emergency_alert(
        documento_id="DOC-TEST-TEP",
        paciente_nome="Carlos Eduardo Mendes",
        diagnostico="Tromboembolismo Pulmonar Agudo (TEP)",
        crm_solicitante="145892-SP",
    )


def test_historico_traz_mensagem_e_status_para_a_aba_de_webhooks():
    # A aba do Streamlit lê al["mensagem"]; antes a chave não existia e a aba quebrava com KeyError
    dispatcher = NotificationDispatcher(mock_mode=True)
    disparar(dispatcher)

    alerta = dispatcher.get_recent_alerts()[0]
    assert "Tromboembolismo" in alerta["mensagem"]
    assert alerta["status"] == "sucesso_mock"
    assert alerta["entregue"] is False
    assert alerta["tentativas"] == 0


def test_sem_url_avisa_e_nao_inventa_latencia(monkeypatch, caplog):
    monkeypatch.delenv("WEBHOOK_EMERGENCY_URL", raising=False)
    with caplog.at_level(logging.WARNING, logger="mediflow.notifications"):
        dispatcher = NotificationDispatcher()
    assert dispatcher.mock_mode is True
    assert "WEBHOOK_EMERGENCY_URL" in caplog.text

    disparar(dispatcher)
    registro = dispatcher.historico_alertas[-1]
    assert registro.latencia_ms == 0.0
    assert "simulado" in registro.resposta_servidor


def test_erro_transitorio_tenta_de_novo_e_entrega(servidor):
    servidor["respostas"] = [503, 200]
    dispatcher = NotificationDispatcher(webhook_url=URL, espera_entre_tentativas=0)

    res = disparar(dispatcher)
    assert res["status_envio"] == "sucesso"
    assert res["tentativas"] == 2
    assert dispatcher.historico_alertas[-1].entregue is True


def test_erro_de_configuracao_nao_tenta_de_novo(servidor, caplog):
    servidor["respostas"] = [404]
    dispatcher = NotificationDispatcher(webhook_url=URL, espera_entre_tentativas=0)

    with caplog.at_level(logging.ERROR, logger="mediflow.notifications"):
        res = disparar(dispatcher)
    assert servidor["chamadas"] == 1
    assert res["status_envio"] == "erro_http_404"
    assert "NÃO entregue" in caplog.text


def test_falha_de_rede_fica_no_historico_como_nao_entregue(servidor, caplog):
    servidor["respostas"] = [httpx.ConnectError("recusada"), httpx.ConnectError("recusada")]
    dispatcher = NotificationDispatcher(webhook_url=URL, espera_entre_tentativas=0)

    with caplog.at_level(logging.ERROR, logger="mediflow.notifications"):
        res = disparar(dispatcher)
    assert res["status_envio"] == "falha_conexao"
    assert res["tentativas"] == 2
    registro = dispatcher.historico_alertas[-1]
    assert registro.entregue is False
    assert registro.payload["documento_id"] == "DOC-TEST-TEP"  # guardado para o reenvio (CARD-18)
    assert "NÃO entregue" in caplog.text
