"""
MediFlow — Motor de Circuit-Breaker SRE & Cliente REST Resiliente
Hackathon ONE G10 — Oracle Next Education & Alura (Equipo 22)

Módulo responsável pela governança de resiliência e desacoplamento entre
o Frontend (Streamlit) e a API Backend (FastAPI), implementando o padrão
Circuit-Breaker com fallback in-process para garantir Zero Downtime.

Squad:
  - Carlos Magno (Tech Lead, SRE/DevOps, IA & Python Core)
  - Fernando Szekut (Agent Integration, Webhooks & Front/UX)
  - Helder (Atlas Data — OCI Storage & SQLite Audit)
  - Alessandro (Marcus Builder — Backend FastAPI & QA)
"""

from __future__ import annotations

import enum
import logging
import os
import threading
import time
from typing import Any, Callable, Dict, Optional, Tuple, Type

import httpx

from mediflow_schemas import DocumentoClinicoInput, ResultadoTriagemOutput

logger = logging.getLogger("mediflow.circuit_breaker")


class CircuitBreakerState(str, enum.Enum):
    """Estados canônicos do Circuit-Breaker."""
    CLOSED = "CLOSED"        # Operação normal: requisições fluem para a API remota
    OPEN = "OPEN"            # Circuito aberto: requisições bloqueadas para a API remota, fallback ativo
    HALF_OPEN = "HALF_OPEN"  # Teste de arrefecimento: permite sondagem para verificar recuperação


class CircuitBreakerOpenException(Exception):
    """Exceção levantada quando o circuito está OPEN e nenhum fallback foi configurado."""
    pass


class CircuitBreaker:
    """
    Implementação SRE de Circuit-Breaker thread-safe para proteção contra
    falhas em cascata e degradação graciosa (Graceful Degradation).
    """

    def __init__(
        self,
        name: str = "fastapi_backend",
        failure_threshold: int = 3,
        recovery_timeout: float = 10.0,
        expected_exceptions: Tuple[Type[Exception], ...] = (
            httpx.RequestError,
            httpx.HTTPStatusError,
            TimeoutError,
            ConnectionError,
            Exception,
        ),
        fallback: Optional[Callable[..., Any]] = None,
    ) -> None:
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exceptions = expected_exceptions
        self.fallback = fallback

        self._lock = threading.RLock()
        self._state = CircuitBreakerState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._total_calls = 0
        self._fallback_calls = 0
        self._last_failure_time: Optional[float] = None
        self._last_state_change: float = time.monotonic()

    @property
    def state(self) -> CircuitBreakerState:
        with self._lock:
            # Se está OPEN, verifica se a janela de recuperação expirou para ir para HALF_OPEN
            if self._state == CircuitBreakerState.OPEN:
                if self._last_failure_time is not None:
                    elapsed = time.monotonic() - self._last_failure_time
                    if elapsed >= self.recovery_timeout:
                        self._transition_to(CircuitBreakerState.HALF_OPEN)
            return self._state

    @property
    def failure_count(self) -> int:
        with self._lock:
            return self._failure_count

    @property
    def fallback_calls(self) -> int:
        with self._lock:
            return self._fallback_calls

    @property
    def total_calls(self) -> int:
        with self._lock:
            return self._total_calls

    def _transition_to(self, new_state: CircuitBreakerState) -> None:
        if self._state != new_state:
            logger.warning(
                f"[CIRCUIT-BREAKER:{self.name}] Transição de estado: {self._state.value} -> {new_state.value} "
                f"(Falhas acumuladas: {self._failure_count})"
            )
            self._state = new_state
            self._last_state_change = time.monotonic()
            if new_state == CircuitBreakerState.CLOSED:
                self._failure_count = 0

    def call(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """
        Executa a função através da proteção do Circuit-Breaker.
        """
        with self._lock:
            self._total_calls += 1
            current_state = self.state

            # Se o circuito estiver OPEN, bloqueia chamada remota e aciona fallback
            if current_state == CircuitBreakerState.OPEN:
                logger.info(f"[CIRCUIT-BREAKER:{self.name}] Chamada interceptada no estado OPEN. Acionando contingência.")
                if self.fallback:
                    self._fallback_calls += 1
                    return self.fallback(*args, **kwargs)
                raise CircuitBreakerOpenException(
                    f"Circuit-Breaker '{self.name}' está OPEN. Requisições externas suspensas."
                )

        # Se CLOSED ou HALF_OPEN, tenta executar a chamada remota
        try:
            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            duration = time.perf_counter() - start_time

            with self._lock:
                self._success_count += 1
                if self._state == CircuitBreakerState.HALF_OPEN:
                    logger.info(
                        f"[CIRCUIT-BREAKER:{self.name}] Teste bem-sucedido em HALF_OPEN ({duration*1000:.1f}ms). "
                        f"Fechando circuito (CLOSED)."
                    )
                    self._transition_to(CircuitBreakerState.CLOSED)
                elif self._state == CircuitBreakerState.CLOSED:
                    # Reseta falhas transitórias após sucesso
                    self._failure_count = 0

            return result

        except self.expected_exceptions as exc:
            with self._lock:
                self._failure_count += 1
                self._last_failure_time = time.monotonic()
                logger.error(
                    f"[CIRCUIT-BREAKER:{self.name}] Falha na chamada ({exc.__class__.__name__}: {exc}). "
                    f"Contagem de falhas: {self._failure_count}/{self.failure_threshold}"
                )

                # Se falhar em HALF_OPEN ou ultrapassar o threshold em CLOSED, abre o circuito
                if self._state == CircuitBreakerState.HALF_OPEN or self._failure_count >= self.failure_threshold:
                    self._transition_to(CircuitBreakerState.OPEN)

                if self.fallback:
                    self._fallback_calls += 1
                    logger.info(f"[CIRCUIT-BREAKER:{self.name}] Acionando fallback in-process pós-falha.")
                    return self.fallback(*args, **kwargs)

                raise exc

    def trip(self) -> None:
        """Abre o circuito manualmente (útil para testes de injeção de caos e manutenção)."""
        with self._lock:
            self._last_failure_time = time.monotonic()
            self._failure_count = self.failure_threshold
            self._transition_to(CircuitBreakerState.OPEN)

    def reset(self) -> None:
        """Reseta o circuito para o estado CLOSED com contadores limpos."""
        with self._lock:
            self._failure_count = 0
            self._last_failure_time = None
            self._transition_to(CircuitBreakerState.CLOSED)

    def get_metrics(self) -> Dict[str, Any]:
        """Retorna telemetria e métricas operacionais do Circuit-Breaker."""
        with self._lock:
            current_state = self.state
            return {
                "name": self.name,
                "state": current_state.value,
                "failure_count": self._failure_count,
                "failure_threshold": self.failure_threshold,
                "recovery_timeout_sec": self.recovery_timeout,
                "total_calls": self._total_calls,
                "success_count": self._success_count,
                "fallback_calls": self._fallback_calls,
                "last_failure_time": self._last_failure_time,
                "uptime_in_state_sec": round(time.monotonic() - self._last_state_change, 2),
            }


class ResilientMediFlowClient:
    """
    Cliente REST de alta resiliência para comunicação entre o Streamlit e a API FastAPI.
    Implementa desacoplamento com Circuit-Breaker e chaveamento transparente
    para motor LangGraph in-process (Zero Downtime).
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = 3.0,
        failure_threshold: int = 3,
        recovery_timeout: float = 8.0,
        local_agent: Optional[Any] = None,
    ) -> None:
        self.base_url = (base_url or os.getenv("MEDIFLOW_API_URL", "http://127.0.0.1:8000")).rstrip("/")
        self.timeout = timeout

        # Inicializa o agente local de contingência caso não seja fornecido
        if local_agent is None:
            try:
                from week3.agent import MediFlowStateGraphAgent
                from week3.notifications import NotificationDispatcher
                from week3.storage import OCIStorageServiceV3
                self.local_agent = MediFlowStateGraphAgent(
                    storage_service=OCIStorageServiceV3(),
                    notification_dispatcher=NotificationDispatcher(),
                )
            except Exception as e:
                logger.warning(f"Erro ao instanciar MediFlowStateGraphAgent para contingência: {e}. Usando mediflow_agent.")
                from mediflow_agent import MediFlowAgentGraph
                self.local_agent = MediFlowAgentGraph()
        else:
            self.local_agent = local_agent

        # Configura o Circuit-Breaker com o fallback in-process
        self.breaker = CircuitBreaker(
            name="fastapi_triagem_client",
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            expected_exceptions=(
                httpx.RequestError,
                httpx.HTTPStatusError,
                httpx.TimeoutException,
                httpx.ConnectError,
                Exception,
            ),
            fallback=self._in_process_fallback,
        )

    def _in_process_fallback(self, documento: DocumentoClinicoInput) -> Tuple[ResultadoTriagemOutput, Dict[str, Any]]:
        """Executa a triagem diretamente na mesma thread via LangGraph (Zero Downtime)."""
        logger.warning(f"⚡ [SRE FALLBACK] Executando triagem in-process para documento {documento.documento_id}")
        start_time = time.perf_counter()
        resultado = self.local_agent.run(documento)
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

        meta = {
            "origem": "fallback_local_in_process",
            "modo": "contingencia_sre",
            "status_circuito": self.breaker.state.value,
            "latencia_ms": latency_ms,
            "aviso": "Backend FastAPI indisponível. Processamento executado localmente via LangGraph (Zero Downtime).",
        }
        return resultado, meta

    def _http_remote_call(self, documento: DocumentoClinicoInput) -> Tuple[ResultadoTriagemOutput, Dict[str, Any]]:
        """Executa a chamada HTTP REST contra a API FastAPI."""
        url = f"{self.base_url}/api/v1/triagem"
        payload_dict = documento.to_dict(exclude_none=True)

        start_time = time.perf_counter()
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(url, json=payload_dict)
            resp.raise_for_status()
            data = resp.json()

        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        if hasattr(ResultadoTriagemOutput, "model_validate"):
            resultado = ResultadoTriagemOutput.model_validate(data)
        else:
            resultado = ResultadoTriagemOutput(**data)

        meta = {
            "origem": "fastapi_rest",
            "modo": "normal",
            "status_circuito": self.breaker.state.value,
            "latencia_ms": latency_ms,
            "url": url,
        }
        return resultado, meta

    def processar_triagem(
        self, documento: DocumentoClinicoInput
    ) -> Tuple[ResultadoTriagemOutput, Dict[str, Any]]:
        """
        Processa a triagem clínica de forma resiliente.
        Tenta chamar a API FastAPI e, em caso de lentidão, timeout ou queda,
        o Circuit-Breaker assume a requisição e executa o fallback in-process.
        """
        return self.breaker.call(self._http_remote_call, documento)

    def check_health(self) -> Dict[str, Any]:
        """Verifica a integridade da API FastAPI e do Circuit-Breaker."""
        url = f"{self.base_url}/health"
        is_reachable = False
        api_data = {}

        try:
            with httpx.Client(timeout=1.0) as client:
                resp = client.get(url)
                if resp.status_code == 200:
                    is_reachable = True
                    api_data = resp.json()
        except Exception:
            is_reachable = False

        return {
            "api_reachable": is_reachable,
            "api_url": self.base_url,
            "api_health": api_data,
            "circuit_breaker": self.breaker.get_metrics(),
        }
