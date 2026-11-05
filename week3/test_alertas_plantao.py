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
    estado = {"respostas": [], "chamadas": 0, "payloads": []}

    class ClienteFalso:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def post(self, url, **kwargs):
            estado["chamadas"] += 1
            estado["payloads"].append(kwargs.get("json"))
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


# -----------------------------------------------------------------------------
# Reenvio manual e histórico de entregas (CARD-18)
# -----------------------------------------------------------------------------

def test_reenvio_entrega_alerta_que_falhou(servidor, caplog):
    servidor["respostas"] = [503, 503, 200]
    dispatcher = NotificationDispatcher(webhook_url=URL, espera_entre_tentativas=0)
    disparar(dispatcher)
    registro = dispatcher.historico_alertas[-1]
    assert registro.entregue is False

    with caplog.at_level(logging.INFO, logger="mediflow.notifications"):
        res = dispatcher.reenviar(registro.alerta_id)

    assert res["status_envio"] == "sucesso"
    assert registro.entregue is True
    assert registro.reenvios == 1
    assert registro.tentativas == 3  # 2 no disparo + 1 no reenvio
    assert registro.ultimo_reenvio is not None
    # mesmo payload, marcado para o receptor poder descartar duplicata
    reenviado = servidor["payloads"][-1]
    assert reenviado["documento_id"] == "DOC-TEST-TEP"
    assert reenviado["reenvio_manual"] == 1
    assert "reenvio_manual" not in registro.payload  # o original fica intacto
    assert len(dispatcher.historico_alertas) == 1  # atualiza o registro, não cria outro


def test_reenvio_que_falha_de_novo_continua_reenviavel(servidor, caplog):
    servidor["respostas"] = [404, 404]
    dispatcher = NotificationDispatcher(webhook_url=URL, espera_entre_tentativas=0)
    disparar(dispatcher)
    alerta_id = dispatcher.historico_alertas[-1].alerta_id

    with caplog.at_level(logging.ERROR, logger="mediflow.notifications"):
        res = dispatcher.reenviar(alerta_id)

    assert res["status_envio"] == "erro_http_404"
    assert "também falhou" in caplog.text
    alerta = dispatcher.get_recent_alerts()[0]
    assert alerta["reenvios"] == 1
    assert alerta["pode_reenviar"] is True


def test_reenvio_nao_repete_alerta_ja_entregue(servidor):
    servidor["respostas"] = [200]
    dispatcher = NotificationDispatcher(webhook_url=URL, espera_entre_tentativas=0)
    disparar(dispatcher)

    res = dispatcher.reenviar(dispatcher.historico_alertas[-1].alerta_id)
    assert res["status_envio"] == "ja_entregue"
    assert servidor["chamadas"] == 1
    assert dispatcher.get_recent_alerts()[0]["pode_reenviar"] is False


def test_reenvio_em_modo_simulado_nao_envia():
    dispatcher = NotificationDispatcher(mock_mode=True)
    disparar(dispatcher)

    res = dispatcher.reenviar(dispatcher.historico_alertas[-1].alerta_id)
    assert res["status_envio"] == "sem_webhook"
    assert dispatcher.get_recent_alerts()[0]["pode_reenviar"] is False


def test_reenvio_de_alerta_desconhecido():
    dispatcher = NotificationDispatcher(mock_mode=True)
    with pytest.raises(KeyError):
        dispatcher.reenviar("naoexiste")


def test_resumo_separa_entregue_falha_e_simulado(servidor):
    servidor["respostas"] = [200, 404]
    dispatcher = NotificationDispatcher(webhook_url=URL, espera_entre_tentativas=0)
    disparar(dispatcher)
    disparar(dispatcher)
    dispatcher.mock_mode = True
    disparar(dispatcher)

    resumo = dispatcher.resumo_entregas()
    assert resumo["total"] == 3
    assert resumo["entregues"] == 1
    assert resumo["nao_entregues"] == 1
    assert resumo["simulados"] == 1
    assert resumo["latencia_media_ms"] is not None  # só os dois envios reais entram na média
    assert len({a["alerta_id"] for a in dispatcher.get_recent_alerts()}) == 3

