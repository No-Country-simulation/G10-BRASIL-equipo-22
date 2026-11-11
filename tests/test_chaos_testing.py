"""
MediFlow — Suíte de Chaos Testing & Resiliência SRE de Serviços Externos
Hackathon ONE G10 — Oracle Next Education & Alura (Equipo 22)
Sprint M5 [CARD-27 / #36]: Executar chaos testing simulando indisponibilidade de serviços externos
Persona Responsável: Arquiteto Carlos Vance (Carlos Magno — Tech Lead & SRE/DevOps)
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest

from mediflow_agent import MediFlowAgentGraph
from mediflow_circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpenException,
    CircuitBreakerState,
    ResilientMediFlowClient,
)
from mediflow_schemas import (
    DestinoRoteamentoEnum,
    DocumentoClinicoInput,
    NivelPrioridadeEnum,
    TipoArquivoEnum,
)
from tests.chaos_injector import ChaosFaultType, ChaosInjector
from week3.agent import (
    SCENARIO_1_ROUTINE,
    SCENARIO_2_URGENCY_TEP,
    SCENARIO_3_AMBIGUOUS_HITL,
    MediFlowStateGraphAgent,
)
from week3.notifications import NotificationDispatcher
from week3.storage import OCIStorageServiceV3


# =============================================================================
# 1. Chaos no LLM: Indisponibilidade HTTP 503 em Fluxo de Rotina
# =============================================================================
def test_chaos_llm_http_503_routine_zero_downtime():
    """Comprova que queda da API de LLM (HTTP 503) não interrompe o fluxo de rotina."""
    injector = ChaosInjector()
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = OCIStorageServiceV3(
            bucket_name="mediflow-chaos-test",
            local_fallback_dir=Path(tmpdir) / "bucket",
            db_path=Path(tmpdir) / "audit.db",
        )
        agent = MediFlowStateGraphAgent(storage_service=storage)

        with injector.fault_llm_failure(status_code=503):
            # Execução sob falha externa
            resultado = agent.run(SCENARIO_1_ROUTINE)

        assert resultado.status == "processado"
        assert resultado.documento_id == "DOC-CLIN-2026-1001"
        assert resultado.classificacao.tipo_documento == "Receituário Médico"
        assert resultado.decisao_roteamento.destino_principal == DestinoRoteamentoEnum.FARMACIA_HOSPITALAR
        assert resultado.decisao_roteamento.requer_auditoria_humana is False
        assert ChaosFaultType.LLM_API_ERROR_503 in injector.report.falhas_injetadas


# =============================================================================
# 2. Chaos no LLM: Indisponibilidade HTTP 500 em Achado Crítico de Urgência (TEP)
# =============================================================================
def test_chaos_llm_http_500_critical_urgency_preserved():
    """Comprova que mesmo com erro 500 no LLM, a vida do paciente crítico é priorizada."""
    injector = ChaosInjector()
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = OCIStorageServiceV3(
            bucket_name="mediflow-chaos-test",
            local_fallback_dir=Path(tmpdir) / "bucket",
            db_path=Path(tmpdir) / "audit.db",
        )
        dispatcher = NotificationDispatcher(mock_mode=True)
        agent = MediFlowStateGraphAgent(storage_service=storage, notification_dispatcher=dispatcher)

        with injector.fault_llm_failure(status_code=500):
            resultado = agent.run(SCENARIO_2_URGENCY_TEP)

        assert resultado.status == "processado"
        assert resultado.classificacao.nivel_prioridade == NivelPrioridadeEnum.URGENTE
        assert resultado.decisao_roteamento.destino_principal == DestinoRoteamentoEnum.FILA_EMERGENCIA_MEDICA
        assert resultado.dados_extraidos.diagnostico_principal == "Tromboembolismo Pulmonar Agudo (TEP)"
        assert resultado.dados_extraidos.cid_sugerido == "I26.9"
        assert len(dispatcher.historico_alertas) >= 1


# =============================================================================
# 3. Chaos de Rede: Timeout Severo (> 5s / ReadTimeout) na Conexão Externa
# =============================================================================
def test_chaos_network_timeout_triggers_sre_fallback():
    """Valida resiliência imediata perante timeout de rede sem travamento do agente."""
    injector = ChaosInjector()
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = OCIStorageServiceV3(
            bucket_name="mediflow-chaos-test",
            local_fallback_dir=Path(tmpdir) / "bucket",
            db_path=Path(tmpdir) / "audit.db",
        )
        agent = MediFlowStateGraphAgent(storage_service=storage)

        with injector.fault_network_timeout(timeout_sec=6.0):
            resultado = agent.run(SCENARIO_1_ROUTINE)

        assert resultado.status == "processado"
        assert resultado.classificacao.score_confianca_classificacao >= 0.85
        assert ChaosFaultType.LLM_NETWORK_TIMEOUT in injector.report.falhas_injetadas


# =============================================================================
# 4. Chaos no OCI Storage: Indisponibilidade de Bucket e Gravação Resiliente
# =============================================================================
def test_chaos_oci_storage_service_error_local_mirror_preserved():
    """Valida integridade dos dados e gravação em espelho local quando o OCI Storage falha."""
    injector = ChaosInjector()
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = OCIStorageServiceV3(
            bucket_name="mediflow-chaos-test",
            local_fallback_dir=Path(tmpdir) / "bucket",
            db_path=Path(tmpdir) / "audit.db",
        )
        agent = MediFlowStateGraphAgent(storage_service=storage)

        with injector.fault_oci_storage():
            resultado = agent.run(SCENARIO_1_ROUTINE)

        assert resultado.status == "processado"
        assert resultado.armazenamento_oci.status_backup == "sucesso"

        # Verifica se o arquivo existe fisicamente no espelho local
        caminho_local = Path(tmpdir) / "bucket" / "mediflow-chaos-test" / resultado.armazenamento_oci.caminho_objeto
        assert caminho_local.exists(), "Espelho local SRE deveria conter o documento preservado."


# =============================================================================
# 5. Chaos no Webhook: Falha HTTP 500 no Receptor do Plantão Médico
# =============================================================================
def test_chaos_webhook_drop_failure_logged_without_crashing():
    """Comprova que falha no servidor de Webhook não interrompe o pipeline e registra para reenvio."""
    injector = ChaosInjector()
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = OCIStorageServiceV3(
            bucket_name="mediflow-chaos-test",
            local_fallback_dir=Path(tmpdir) / "bucket",
            db_path=Path(tmpdir) / "audit.db",
        )
        # Dispatcher com URL configurada e retentativa rápida
        dispatcher = NotificationDispatcher(
            webhook_url="https://hospital-emergency.internal/api/webhook",
            max_tentativas=2,
            espera_entre_tentativas=0.01,
        )
        agent = MediFlowStateGraphAgent(storage_service=storage, notification_dispatcher=dispatcher)

        with injector.fault_webhook_failure(status_code=500):
            resultado = agent.run(SCENARIO_2_URGENCY_TEP)

        assert resultado.status == "processado"
        assert resultado.classificacao.nivel_prioridade == NivelPrioridadeEnum.URGENTE
        assert len(dispatcher.historico_alertas) == 1

        alerta = dispatcher.historico_alertas[0]
        assert "erro_http_500" in alerta.status_entrega
        assert alerta.alerta_id is not None
        assert alerta.tentativas == 2


# =============================================================================
# 6. Chaos Extremo: Blackout Externo Simultâneo (LLM 503 + OCI Down + Webhook Drop)
# =============================================================================
def test_chaos_complete_external_blackout_resilience():
    """Valida sobrevivência do pipeline no pior cenário (todas as APIs de terceiros indisponíveis)."""
    injector = ChaosInjector()
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = OCIStorageServiceV3(
            bucket_name="mediflow-chaos-test",
            local_fallback_dir=Path(tmpdir) / "bucket",
            db_path=Path(tmpdir) / "audit.db",
        )
        dispatcher = NotificationDispatcher(
            webhook_url="https://hospital-emergency.internal/api/webhook",
            max_tentativas=1,
            espera_entre_tentativas=0.01,
        )
        agent = MediFlowStateGraphAgent(storage_service=storage, notification_dispatcher=dispatcher)

        with injector.fault_matrix_all_external_down():
            resultado = agent.run(SCENARIO_2_URGENCY_TEP)

        # O agente sobreviveu 100% sem unhandled exception
        assert resultado.status == "processado"
        assert resultado.classificacao.nivel_prioridade == NivelPrioridadeEnum.URGENTE
        assert resultado.decisao_roteamento.destino_principal == DestinoRoteamentoEnum.FILA_EMERGENCIA_MEDICA

        # Histórico SQLite foi registrado com sucesso
        historico = storage.get_audit_history(limit=5)
        assert len(historico) >= 1
        assert historico[0]["documento_id"] == "DOC-CLIN-2026-8942"


# =============================================================================
# 7. Chaos no Backend FastAPI & Circuit-Breaker: Transição para OPEN e Fallback
# =============================================================================
def test_chaos_circuit_breaker_trips_to_open_under_api_downtime():
    """Comprova proteção do Circuit-Breaker SRE perante indisponibilidade do backend FastAPI."""
    client = ResilientMediFlowClient(
        base_url="http://backend-fora-do-ar:9999",
        failure_threshold=2,
        recovery_timeout=5.0,
    )
    cb = client.breaker

    # Injeta falha de conexão do cliente HTTP simulando queda do container FastAPI
    mock_failing_post = MagicMock(side_effect=httpx.ConnectError("Connection refused by host"))

    with patch.object(httpx.Client, "post", mock_failing_post):
        # 1ª chamada cai no fallback in-process
        res1, meta1 = client.processar_triagem(SCENARIO_1_ROUTINE)
        assert res1.status == "processado"
        assert meta1["modo"] == "contingencia_sre"
        assert cb.failure_count == 1
        assert cb.state == CircuitBreakerState.CLOSED

        # 2ª chamada atinge threshold e abre o circuito
        res2, meta2 = client.processar_triagem(SCENARIO_1_ROUTINE)
        assert res2.status == "processado"
        assert meta2["modo"] == "contingencia_sre"
        assert cb.state == CircuitBreakerState.OPEN

        # 3ª chamada com circuito OPEN não faz I/O e chaveia diretamente
        res3, meta3 = client.processar_triagem(SCENARIO_2_URGENCY_TEP)
        assert res3.classificacao.nivel_prioridade == NivelPrioridadeEnum.URGENTE
        assert cb.state == CircuitBreakerState.OPEN


# =============================================================================
# 8. Chaos com Payload Danificado / Caracteres Estranhos sob Falha de Rede
# =============================================================================
def test_chaos_corrupted_payload_graceful_hitl_quarantine():
    """Valida retenção segura de payload ambíguo/corrompido sob falha de serviços externos."""
    doc_corrompido = DocumentoClinicoInput(
        documento_id="DOC-CHAOS-CORRUPT-999",
        tipo_arquivo=TipoArquivoEnum.TEXTO,
        documento_texto="Texto ilegível ??? [rasura total] sem assinatura e sem dados de identificação.",
        canal_origem="Triagem_Caos",
    )

    injector = ChaosInjector()
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = OCIStorageServiceV3(
            bucket_name="mediflow-chaos-test",
            local_fallback_dir=Path(tmpdir) / "bucket",
            db_path=Path(tmpdir) / "audit.db",
        )
        agent = MediFlowStateGraphAgent(storage_service=storage)

        with injector.fault_llm_failure(status_code=503):
            resultado = agent.run(doc_corrompido)

        assert resultado.status == "retido_auditoria_humana"
        assert resultado.decisao_roteamento.requer_auditoria_humana is True
        assert resultado.decisao_roteamento.destino_principal == DestinoRoteamentoEnum.FILA_REVISAO_HUMANA


# =============================================================================
# 9. Retentativa do Dispatcher perante Falha HTTP Transitória com Recuperação
# =============================================================================
def test_chaos_webhook_transient_failure_then_success():
    """Valida recuperação automática do dispatcher em falha HTTP transitória (retry exponencial)."""
    dispatcher = NotificationDispatcher(
        webhook_url="https://hospital-emergency.internal/api/webhook",
        max_tentativas=2,
        espera_entre_tentativas=0.01,
    )

    # Primeira tentativa retorna 503, segunda retorna 200 (sucesso)
    mock_resp_fail = MagicMock(spec=httpx.Response, status_code=503, text="Service Unavailable", is_success=False)
    mock_resp_ok = MagicMock(spec=httpx.Response, status_code=200, text="OK", is_success=True)

    with patch.object(httpx.Client, "post", side_effect=[mock_resp_fail, mock_resp_ok]):
        res = dispatcher.dispatch_emergency_alert(
            documento_id="DOC-RETRY-001",
            paciente_nome="Jose Santos",
            diagnostico="TEP Agudo",
            crm_solicitante="123456-SP",
        )

    assert res["status_envio"] == "sucesso"
    assert res["tentativas"] == 2
    assert dispatcher.historico_alertas[-1].entregue is True
