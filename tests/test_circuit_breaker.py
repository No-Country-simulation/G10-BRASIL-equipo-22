"""
MediFlow — Testes Automatizados do Motor de Circuit-Breaker SRE
Hackathon ONE G10 — Oracle Next Education & Alura (Equipo 22)
Sprint M5 [CARD-25 / #34]: Conectar frontend Streamlit à API FastAPI com circuit-breaker SRE
"""

import time
from unittest.mock import MagicMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from mediflow_circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpenException,
    CircuitBreakerState,
    ResilientMediFlowClient,
)
from mediflow_schemas import DocumentoClinicoInput, TipoArquivoEnum
from week3.agent import SCENARIO_1_ROUTINE, SCENARIO_2_URGENCY_TEP
from week3.api import app


def test_circuit_breaker_initial_state_closed():
    """Valida o estado inicial do Circuit-Breaker (CLOSED, contadores zerados)."""
    cb = CircuitBreaker(name="test_cb", failure_threshold=3, recovery_timeout=5.0)
    assert cb.state == CircuitBreakerState.CLOSED
    assert cb.failure_count == 0
    assert cb.total_calls == 0
    assert cb.fallback_calls == 0


def test_circuit_breaker_normal_success_flow():
    """Valida execução bem-sucedida em regime normal."""
    cb = CircuitBreaker(name="test_cb", failure_threshold=3)
    mock_func = MagicMock(return_value="OK")

    result = cb.call(mock_func, 10, key="value")

    assert result == "OK"
    assert cb.state == CircuitBreakerState.CLOSED
    assert cb.failure_count == 0
    assert cb.total_calls == 1
    mock_func.assert_called_once_with(10, key="value")


def test_circuit_breaker_trips_to_open_after_threshold():
    """Valida que o circuito abre após atingir o limiar de falhas consecutivas."""
    cb = CircuitBreaker(name="test_cb", failure_threshold=3, recovery_timeout=10.0)
    mock_failing_func = MagicMock(side_effect=httpx.ConnectError("Connection refused"))

    for i in range(2):
        with pytest.raises(httpx.ConnectError):
            cb.call(mock_failing_func)
        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.failure_count == i + 1

    # 3ª falha atinge o threshold -> estado deve mudar para OPEN
    with pytest.raises(httpx.ConnectError):
        cb.call(mock_failing_func)

    assert cb.state == CircuitBreakerState.OPEN
    assert cb.failure_count == 3


def test_circuit_breaker_open_blocks_calls_and_executes_fallback():
    """Valida que no estado OPEN a chamada remota é bloqueada e o fallback é acionado."""
    fallback_mock = MagicMock(return_value="FALLBACK_RESULT")
    cb = CircuitBreaker(
        name="test_cb",
        failure_threshold=2,
        recovery_timeout=10.0,
        fallback=fallback_mock,
    )

    # Força 2 falhas para abrir o circuito
    failing_func = MagicMock(side_effect=TimeoutError("Timeout"))
    cb.call(failing_func)  # Falha 1 (aciona fallback)
    cb.call(failing_func)  # Falha 2 -> agora OPEN (aciona fallback)
    assert cb.state == CircuitBreakerState.OPEN

    # Nova chamada enquanto OPEN: failing_func NÃO deve ser chamada novamente
    failing_func.reset_mock()
    fallback_mock.reset_mock()

    result = cb.call(failing_func, "doc_123")

    assert result == "FALLBACK_RESULT"
    failing_func.assert_not_called()
    fallback_mock.assert_called_once_with("doc_123")
    assert cb.fallback_calls == 3


def test_circuit_breaker_open_raises_without_fallback():
    """Valida que se não houver fallback configurado, levanta CircuitBreakerOpenException."""
    cb = CircuitBreaker(name="test_cb", failure_threshold=1)
    with pytest.raises(Exception):
        cb.call(MagicMock(side_effect=Exception("Crash")))

    assert cb.state == CircuitBreakerState.OPEN

    with pytest.raises(CircuitBreakerOpenException) as exc_info:
        cb.call(MagicMock())

    assert "está OPEN" in str(exc_info.value)


def test_circuit_breaker_recovers_to_half_open_and_resets_to_closed():
    """Valida ciclo completo: CLOSED -> OPEN -> HALF_OPEN -> CLOSED."""
    cb = CircuitBreaker(
        name="test_cb",
        failure_threshold=1,
        recovery_timeout=0.15,  # 150ms para teste ágil
    )

    # 1. Falha única abre o circuito
    with pytest.raises(Exception):
        cb.call(MagicMock(side_effect=Exception("Falha")))
    assert cb.state == CircuitBreakerState.OPEN

    # 2. Aguarda expiração da janela de recuperação
    time.sleep(0.2)
    assert cb.state == CircuitBreakerState.HALF_OPEN

    # 3. Chamada de teste tem sucesso -> Circuito fecha (CLOSED)
    success_func = MagicMock(return_value="RECOVERED")
    result = cb.call(success_func)

    assert result == "RECOVERED"
    assert cb.state == CircuitBreakerState.CLOSED
    assert cb.failure_count == 0


def test_circuit_breaker_half_open_failure_immediately_reopens():
    """Valida que se a chamada falhar em HALF_OPEN, o circuito reabre imediatamente."""
    cb = CircuitBreaker(
        name="test_cb",
        failure_threshold=3,
        recovery_timeout=0.1,
    )
    cb.trip()  # Abre manualmente
    assert cb.state == CircuitBreakerState.OPEN

    time.sleep(0.15)
    assert cb.state == CircuitBreakerState.HALF_OPEN

    # Falha na chamada de teste do HALF_OPEN
    with pytest.raises(ValueError):
        cb.call(MagicMock(side_effect=ValueError("Ainda instável")))

    assert cb.state == CircuitBreakerState.OPEN


def test_circuit_breaker_manual_trip_and_reset():
    """Valida controle operacional de trip e reset manual."""
    cb = CircuitBreaker(name="manual_test")
    assert cb.state == CircuitBreakerState.CLOSED

    cb.trip()
    assert cb.state == CircuitBreakerState.OPEN

    cb.reset()
    assert cb.state == CircuitBreakerState.CLOSED
    assert cb.failure_count == 0


def test_resilient_mediflow_client_fallback_on_unreachable_api():
    """
    Testa o cliente desacoplado contra uma porta inexistente:
    deve acionar o fallback in-process com Zero Downtime.
    """
    client = ResilientMediFlowClient(
        base_url="http://127.0.0.1:59999",  # Porta inacessível
        timeout=0.5,
        failure_threshold=1,
        recovery_timeout=5.0,
    )

    doc = SCENARIO_2_URGENCY_TEP
    resultado, meta = client.processar_triagem(doc)

    assert resultado.documento_id == doc.documento_id
    assert resultado.status == "processado"
    assert meta["origem"] == "fallback_local_in_process"
    assert meta["modo"] == "contingencia_sre"
    assert "Zero Downtime" in meta["aviso"]
    assert client.breaker.state == CircuitBreakerState.OPEN


def test_resilient_mediflow_client_with_fastapi_rest_success():
    """
    Testa chamada REST bem-sucedida contra a API FastAPI real usando TestClient.
    """
    test_fastapi = TestClient(app)
    client = ResilientMediFlowClient(base_url="http://testserver", timeout=2.0)

    # Patch do httpx.Client para direcionar as requisições ao TestClient do FastAPI
    with patch("httpx.Client") as mock_httpx:
        mock_instance = MagicMock()
        mock_httpx.return_value.__enter__.return_value = mock_instance

        # Simula resposta 200 da API FastAPI
        doc = SCENARIO_1_ROUTINE
        real_response = test_fastapi.post(
            "/api/v1/triagem",
            json=doc.to_dict(exclude_none=True),
        )
        assert real_response.status_code == 200

        mock_instance.post.return_value = real_response

        resultado, meta = client.processar_triagem(doc)

        assert resultado.documento_id == doc.documento_id
        assert meta["origem"] == "fastapi_rest"
        assert meta["modo"] == "normal"
        assert meta["status_circuito"] == "CLOSED"
        assert client.breaker.state == CircuitBreakerState.CLOSED


def test_resilient_client_check_health():
    """Valida a telemetria do endpoint de saúde do cliente."""
    client = ResilientMediFlowClient(base_url="http://127.0.0.1:59999")
    health = client.check_health()

    assert health["api_reachable"] is False
    assert "circuit_breaker" in health
    assert health["circuit_breaker"]["state"] == "CLOSED"
