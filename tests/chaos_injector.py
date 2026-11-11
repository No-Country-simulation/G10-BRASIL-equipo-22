"""
MediFlow — Injetor de Falhas de Chaos Engineering & Resiliência SRE
Hackathon ONE G10 — Oracle Next Education & Alura (Equipo 22)
Sprint M5 [CARD-27 / #36]: Executar chaos testing simulando indisponibilidade de serviços externos
Persona Responsável: Arquiteto Carlos Vance (Carlos Magno — Tech Lead & SRE/DevOps)

Matriz de 4 Vetores de Falha:
1. Queda da API de LLM (NVIDIA NIM / Gemini com HTTP 500/503 ou ConnectionError)
2. Timeout de rede severo (> 5s / ReadTimeout / ConnectTimeout)
3. Falha ou indisponibilidade de escrita no OCI Object Storage
4. Queda / indisponibilidade do despachador de Webhooks de emergência
"""

from __future__ import annotations

import contextlib
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Generator, List, Optional
from unittest.mock import MagicMock, patch

import httpx

logger = logging.getLogger("mediflow.chaos")


class ChaosFaultType(str, Enum):
    LLM_API_ERROR_503 = "LLM_API_ERROR_503"
    LLM_NETWORK_TIMEOUT = "LLM_NETWORK_TIMEOUT"
    OCI_STORAGE_ERROR = "OCI_STORAGE_ERROR"
    WEBHOOK_DROP_FAILURE = "WEBHOOK_DROP_FAILURE"
    STORAGE_DISK_FULL = "STORAGE_DISK_FULL"


@dataclass
class ChaosInjectionReport:
    """Relatório de execução de injeção de caos."""

    falhas_injetadas: List[ChaosFaultType] = field(default_factory=list)
    tentativas_interceptadas: int = 0
    fallback_ativado: bool = False
    dados_preservados: bool = True
    excecao_nao_tratada: bool = False
    detalhes: Dict[str, Any] = field(default_factory=dict)


class ChaosInjector:
    """
    Gerenciador e orquestrador de injeção de falhas para Chaos Engineering.
    Permite validar a resiliência Zero Downtime de todos os componentes do MediFlow.
    """

    def __init__(self) -> None:
        self.report = ChaosInjectionReport()

    @contextlib.contextmanager
    def fault_llm_failure(self, status_code: int = 503) -> Generator[ChaosInjector, None, None]:
        """
        Injeta falha HTTP 500/502/503 ou indisponibilidade na API externa do LLM (NVIDIA NIM / Gemini).
        Comprova que o nó de classificação do agente chaveia graciosamente para o motor local.
        """
        self.report.falhas_injetadas.append(ChaosFaultType.LLM_API_ERROR_503)
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = status_code
        mock_response.text = f'{{"error": "Service Unavailable", "code": {status_code}}}'
        mock_response.is_success = False

        original_post = httpx.Client.post

        def mock_post(url: Any, *args: Any, **kwargs: Any) -> httpx.Response:
            url_str = str(url)
            if "integrate.api.nvidia.com" in url_str or "generativelanguage.googleapis.com" in url_str:
                self.report.tentativas_interceptadas += 1
                return mock_response
            return original_post(url, *args, **kwargs)

        with patch.object(httpx.Client, "post", side_effect=mock_post):
            yield self

    @contextlib.contextmanager
    def fault_network_timeout(self, timeout_sec: float = 6.0) -> Generator[ChaosInjector, None, None]:
        """
        Injeta timeout severo de rede simulando latência infinita ou perda de pacotes externa.
        """
        self.report.falhas_injetadas.append(ChaosFaultType.LLM_NETWORK_TIMEOUT)
        original_post = httpx.Client.post

        def mock_post(url: Any, *args: Any, **kwargs: Any) -> httpx.Response:
            url_str = str(url)
            if "integrate.api.nvidia.com" in url_str or "generativelanguage.googleapis.com" in url_str:
                self.report.tentativas_interceptadas += 1
                raise httpx.ReadTimeout(f"Chaos injected: Network timed out after {timeout_sec}s")
            return original_post(url, *args, **kwargs)

        with patch.object(httpx.Client, "post", side_effect=mock_post):
            yield self

    @contextlib.contextmanager
    def fault_oci_storage(self) -> Generator[ChaosInjector, None, None]:
        """
        Injeta erro de API ou indisponibilidade de escrita no OCI Object Storage.
        Comprova que o fallback local SRE grava o documento sem perda de dados.
        """
        self.report.falhas_injetadas.append(ChaosFaultType.OCI_STORAGE_ERROR)

        def mock_put_object(*args: Any, **kwargs: Any) -> None:
            self.report.tentativas_interceptadas += 1
            raise RuntimeError("Chaos injected: OCI Object Storage ServiceError (500 - BucketUnavailable)")

        with patch("week3.storage.OCIStorageServiceV3._init_oci_client", return_value=MagicMock(put_object=mock_put_object)):
            yield self

    @contextlib.contextmanager
    def fault_webhook_failure(self, status_code: int = 500) -> Generator[ChaosInjector, None, None]:
        """
        Injeta falha no endpoint de Webhook hospitalar (HTTP 500/504 ou conexão recusada).
        Comprova que o dispatcher registra a falha no histórico para reenvio sem interromper a triagem.
        """
        self.report.falhas_injetadas.append(ChaosFaultType.WEBHOOK_DROP_FAILURE)
        original_post = httpx.Client.post

        def mock_post(url: Any, *args: Any, **kwargs: Any) -> httpx.Response:
            url_str = str(url).lower()
            if "webhook" in url_str or "hospital" in url_str or "alert" in url_str:
                self.report.tentativas_interceptadas += 1
                mock_resp = MagicMock(spec=httpx.Response)
                mock_resp.status_code = status_code
                mock_resp.text = f"Webhook Gateway Error {status_code}"
                mock_resp.is_success = False
                return mock_resp
            return original_post(url, *args, **kwargs)

        with patch.object(httpx.Client, "post", side_effect=mock_post):
            yield self

    @contextlib.contextmanager
    def fault_matrix_all_external_down(self) -> Generator[ChaosInjector, None, None]:
        """
        Injeta o pior cenário possível (Blackout Externo Total):
        - LLM API indisponível (HTTP 503)
        - Webhook receptor com falha de conexão (HTTP 500)
        - OCI remoto indisponível
        O sistema deve sobreviver 100%, concluindo a triagem do paciente com persistência local.
        """
        self.report.falhas_injetadas.extend([
            ChaosFaultType.LLM_API_ERROR_503,
            ChaosFaultType.WEBHOOK_DROP_FAILURE,
            ChaosFaultType.OCI_STORAGE_ERROR,
        ])

        mock_llm_503 = MagicMock(spec=httpx.Response)
        mock_llm_503.status_code = 503
        mock_llm_503.text = '{"error": "LLM Service Unavailable"}'
        mock_llm_503.is_success = False

        mock_wh_500 = MagicMock(spec=httpx.Response)
        mock_wh_500.status_code = 500
        mock_wh_500.text = "Webhook Server Error 500"
        mock_wh_500.is_success = False

        original_post = httpx.Client.post

        def mock_post_unified(url: Any, *args: Any, **kwargs: Any) -> httpx.Response:
            url_str = str(url).lower()
            self.report.tentativas_interceptadas += 1
            if "integrate.api.nvidia.com" in url_str or "generativelanguage.googleapis.com" in url_str:
                return mock_llm_503
            if "webhook" in url_str or "hospital" in url_str or "alert" in url_str:
                return mock_wh_500
            return original_post(url, *args, **kwargs)

        with self.fault_oci_storage():
            with patch.object(httpx.Client, "post", side_effect=mock_post_unified):
                yield self
