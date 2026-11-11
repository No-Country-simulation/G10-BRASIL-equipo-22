"""
MediFlow — Testes Automatizados de Otimização de Latência e Fast-Path Heurístico
Hackathon ONE G10 — Oracle Next Education & Alura (Equipo 22)
Sprint M5 [CARD-26 / #35]: Otimizar tempos de inferência reduzindo latência média para < 3s
Persona Responsável: Arquiteto Carlos Vance (Carlos Magno — Tech Lead & IA Core)
"""

import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mediflow_agent import MediFlowAgentGraph
from mediflow_fast_path import (
    COMPACT_SYSTEM_PROMPT,
    CRITICAL_EMERGENCY_FINDINGS,
    FastPathEngine,
    estimate_prompt_tokens,
)
from mediflow_schemas import (
    DestinoRoteamentoEnum,
    DocumentoClinicoInput,
    NivelPrioridadeEnum,
    TipoArquivoEnum,
)
from week3.agent import (
    SCENARIO_1_ROUTINE,
    SCENARIO_2_URGENCY_TEP,
    SCENARIO_3_AMBIGUOUS_HITL,
    MediFlowStateGraphAgent,
)
from week3.notifications import NotificationDispatcher
from week3.storage import OCIStorageServiceV3


# =============================================================================
# 1. Validação do Prompt Compacto (< 300 Tokens)
# =============================================================================
def test_compact_system_prompt_token_budget():
    """Valida que o prompt compacto de sistema possui menos de 300 tokens e schema estrito."""
    token_count = estimate_prompt_tokens(COMPACT_SYSTEM_PROMPT)
    char_count = len(COMPACT_SYSTEM_PROMPT)

    assert token_count < 300, f"Prompt compacto excedeu 300 tokens: {token_count}"
    assert char_count < 1000, f"Prompt compacto excedeu 1000 caracteres: {char_count}"

    # Verificação de elementos contratuais essenciais
    assert "JSON estrito" in COMPACT_SYSTEM_PROMPT
    assert "tipo_documento" in COMPACT_SYSTEM_PROMPT
    assert "especialidade" in COMPACT_SYSTEM_PROMPT
    assert "nivel_prioridade" in COMPACT_SYSTEM_PROMPT
    assert "score_confianca_classificacao" in COMPACT_SYSTEM_PROMPT
    assert "paciente" in COMPACT_SYSTEM_PROMPT
    assert "medico_solicitante" in COMPACT_SYSTEM_PROMPT
    assert "TEP/Embolia (I26.9)" in COMPACT_SYSTEM_PROMPT
    assert "IAM (I21.9)" in COMPACT_SYSTEM_PROMPT
    assert "Revisao_Humana" in COMPACT_SYSTEM_PROMPT


# =============================================================================
# 2. Fast-Path Heurístico: Cenário de Rotina (< 100ms)
# =============================================================================
def test_fast_path_latency_sub_100ms_routine():
    """Valida execução ultra-rápida do Fast-Path para receita médica de rotina (< 100ms)."""
    engine = FastPathEngine(confidence_threshold=0.85)

    res = engine.process(SCENARIO_1_ROUTINE.documento_texto)

    assert res.is_fast_path is True
    assert res.latencia_ms < 50.0, f"Latência do Fast-Path excedeu 50ms: {res.latencia_ms}ms"
    assert res.classificacao.tipo_documento == "Receituário Médico"
    assert res.classificacao.nivel_prioridade == NivelPrioridadeEnum.ROTINA
    assert res.score_confianca >= 0.85

    assert res.dados_extraidos.paciente.nome == "Mariana Costa Souza"
    assert res.dados_extraidos.paciente.idade == 34
    assert res.dados_extraidos.medico_solicitante.crm == "198432-SP"
    assert res.dados_extraidos.medicamentos_prescritos is not None
    assert len(res.dados_extraidos.medicamentos_prescritos) > 0


# =============================================================================
# 3. Fast-Path Heurístico: Cenário de Urgência Crítica (< 100ms)
# =============================================================================
def test_fast_path_latency_sub_100ms_urgency_tep():
    """Valida detecção imediata de TEP Agudo via Fast-Path com prioridade Urgente e CID I26.9."""
    engine = FastPathEngine(confidence_threshold=0.85)

    res = engine.process(SCENARIO_2_URGENCY_TEP.documento_texto)

    assert res.is_fast_path is True
    assert res.latencia_ms < 50.0, f"Latência do Fast-Path excedeu 50ms: {res.latencia_ms}ms"
    assert res.classificacao.nivel_prioridade == NivelPrioridadeEnum.URGENTE
    assert res.score_confianca >= 0.95
    assert res.dados_extraidos.diagnostico_principal == "Tromboembolismo Pulmonar Agudo (TEP)"
    assert res.dados_extraidos.cid_sugerido == "I26.9"
    assert res.dados_extraidos.paciente.nome == "Carlos Eduardo Mendes"
    assert res.dados_extraidos.medico_solicitante.crm == "145892-SP"


# =============================================================================
# 4. Fast-Path: Detecção Determinística de Ambiguidade / HitL
# =============================================================================
def test_fast_path_ambiguous_hitl_detection():
    """Valida detecção determinística de rasuras e retenção para HitL sem chamada de LLM."""
    engine = FastPathEngine(confidence_threshold=0.85)

    res = engine.process(SCENARIO_3_AMBIGUOUS_HITL.documento_texto)

    assert res.is_fast_path is True
    assert res.latencia_ms < 50.0
    assert res.classificacao.nivel_prioridade == NivelPrioridadeEnum.REVISAO_HUMANA
    assert res.score_confianca < 0.85
    assert any("rasurado" in m or "ilegíveis" in m for m in res.motivos)


# =============================================================================
# 5. Fast-Path: Delegação para LLM quando Texto Não Possui Padrão Clínico
# =============================================================================
def test_fast_path_unstructured_text_fallback():
    """Valida que texto livre sem campos clínicos estruturados desabilita o Fast-Path."""
    engine = FastPathEngine(confidence_threshold=0.85)
    texto_livre = "Reunião de alinhamento com equipe de TI para planejamento do sprint da semana."

    res = engine.process(texto_livre)

    assert res.is_fast_path is False
    assert res.score_confianca < 0.85


# =============================================================================
# 6. Detecção Abrangente de Múltiplas Patologias Críticas
# =============================================================================
@pytest.mark.parametrize(
    "termo_critico,diag_esperado,cid_esperado",
    [
        ("Paciente com infarto agudo do miocardio em curso.", "Infarto Agudo do Miocárdio (IAM)", "I21.9"),
        ("Sinais evidentes de avc isquemico com hemiplegia.", "Acidente Vascular Cerebral Isquêmico Agudo", "I63.9"),
        ("Quadro de choque septico refratario a volume.", "Sepse Grave / Choque Séptico", "A41.9"),
        ("RX evidencia pneumotorax hipertensivo a direita.", "Pneumotórax Hipertensivo", "J93.0"),
    ],
)
def test_fast_path_critical_pathologies(termo_critico, diag_esperado, cid_esperado):
    """Valida que todas as patologias críticas de risco de vida ativam Fast-Path Urgente."""
    engine = FastPathEngine()
    res = engine.process(f"Paciente: Jose Santos. Solicitante: Dr. Silva CRM-SP 123456. {termo_critico}")

    assert res.is_fast_path is True
    assert res.classificacao.nivel_prioridade == NivelPrioridadeEnum.URGENTE
    assert res.dados_extraidos.diagnostico_principal == diag_esperado
    assert res.dados_extraidos.cid_sugerido == cid_esperado
    assert res.score_confianca >= 0.95


# =============================================================================
# 7. Integração LangGraph StateGraph (week3/agent.py) com Fast-Path
# =============================================================================
def test_langgraph_agent_executes_with_fast_path():
    """Valida execução completa do StateGraph utilizando Fast-Path com persistência e log."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = OCIStorageServiceV3(
            bucket_name="mediflow-fastpath-test",
            local_fallback_dir=Path(tmpdir) / "bucket",
            db_path=Path(tmpdir) / "audit.db",
        )
        dispatcher = NotificationDispatcher(mock_mode=True)
        agent = MediFlowStateGraphAgent(storage_service=storage, notification_dispatcher=dispatcher)

        # 1. Executa cenário de rotina
        res_rotina = agent.run(SCENARIO_1_ROUTINE)
        assert res_rotina.status == "processado"
        assert res_rotina.decisao_roteamento.destino_principal == DestinoRoteamentoEnum.FARMACIA_HOSPITALAR

        # 2. Executa cenário de urgência
        res_urg = agent.run(SCENARIO_2_URGENCY_TEP)
        assert res_urg.status == "processado"
        assert res_urg.decisao_roteamento.destino_principal == DestinoRoteamentoEnum.FILA_EMERGENCIA_MEDICA

        # 3. Verifica registro de telemetria no histórico SQLite
        historico = storage.get_audit_history(limit=5)
        assert len(historico) >= 2
        provedores = [reg["provedor_ia"] for reg in historico]
        assert any("Fast-Path" in p for p in provedores)


# =============================================================================
# 8. Integração MediFlowAgentGraph (mediflow_agent.py) com Fast-Path
# =============================================================================
def test_mediflow_agent_graph_executes_with_fast_path():
    """Valida que o agente original MediFlowAgentGraph também utiliza Fast-Path com sucesso."""
    with tempfile.TemporaryDirectory() as tmpdir:
        from oci_storage import OCIStorageService

        storage = OCIStorageService(local_fallback_dir=Path(tmpdir) / "bucket")
        agent = MediFlowAgentGraph(storage_service=storage)

        resultado = agent.run(SCENARIO_1_ROUTINE)

        assert resultado.status == "processado"
        assert resultado.classificacao.tipo_documento == "Receituário Médico"
        assert resultado.classificacao.score_confianca_classificacao >= 0.85
        assert resultado.decisao_roteamento.destino_principal == DestinoRoteamentoEnum.FARMACIA_HOSPITALAR


# =============================================================================
# 9. Verificação de Invocação de LLM com Prompt Compacto quando Fast-Path Não Aplica
# =============================================================================
def test_llm_compact_prompt_mock_invocation():
    """Valida chaveamento para LLM com prompt compacto quando o documento exige inferência multimodal."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = OCIStorageServiceV3(
            bucket_name="mediflow-llm-test",
            local_fallback_dir=Path(tmpdir) / "bucket",
            db_path=Path(tmpdir) / "audit.db",
        )
        agent = MediFlowStateGraphAgent(storage_service=storage)

        # Mock da chamada NVIDIA NIM
        mock_llm_response = {
            "tipo_documento": "Laudo Especializado",
            "especialidade": "Neurologia",
            "nivel_prioridade": "Rotina",
            "score_confianca_classificacao": 0.94,
            "paciente": {"nome": "Lucas Martins", "idade": 45},
            "medico_solicitante": {"nome": "Dra. Ana Costa", "crm": "887766-SP"},
            "exame_realizado": "Eletroencefalograma",
            "diagnostico_principal": "Traçado normal em vigília",
            "cid_sugerido": "R94.0",
        }

        # Cria documento simulando anexo ou texto livre não estruturado
        doc_multimodal = DocumentoClinicoInput(
            documento_id="DOC-MULTIMODAL-001",
            tipo_arquivo=TipoArquivoEnum.TEXTO,
            documento_texto="Texto clínico narrativo sem formato padrão de cabeçalho hospitalar.",
            canal_origem="Neurologia_Externa",
        )

        with patch.object(agent, "_call_nvidia_nim", return_value=mock_llm_response) as mock_call:
            res = agent.run(doc_multimodal)
            mock_call.assert_called_once()
            assert res.classificacao.tipo_documento == "Laudo Especializado"
            assert res.dados_extraidos.paciente.nome == "Lucas Martins"


# =============================================================================
# 10. Benchmark de Latência Média (< 3.0s) em Conformidade com o CARD-26
# =============================================================================
def test_average_latency_strictly_under_3_seconds():
    """
    Comprova que a latência média de inferência em 3 cenários clínicos é < 3.0 segundos.
    (Com o motor Fast-Path, a latência média fica abaixo de 50 milissegundos).
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = OCIStorageServiceV3(
            bucket_name="mediflow-bench-test",
            local_fallback_dir=Path(tmpdir) / "bucket",
            db_path=Path(tmpdir) / "audit.db",
        )
        agent = MediFlowStateGraphAgent(storage_service=storage)

        cenarios = [SCENARIO_1_ROUTINE, SCENARIO_2_URGENCY_TEP, SCENARIO_3_AMBIGUOUS_HITL]
        latencias: list[float] = []

        for doc in cenarios:
            t0 = time.perf_counter()
            agent.run(doc)
            latencias.append(time.perf_counter() - t0)

        latencia_media_s = sum(latencias) / len(latencias)
        latencia_max_s = max(latencias)

        # Requisito CARD-26: Latência média < 3.0s
        assert latencia_media_s < 3.0, f"Latência média {latencia_media_s:.3f}s excedeu 3.0s"
        assert latencia_max_s < 3.0, f"Latência máxima {latencia_max_s:.3f}s excedeu 3.0s"
        # Super-otimização: Fast-Path opera em milissegundos (< 0.2s por documento)
        assert latencia_media_s < 0.20, f"Fast-Path deveria operar em < 200ms: {latencia_media_s:.3f}s"


# =============================================================================
# 11. Teste de Throughput e Carga Rápida (50 chamadas sequenciais)
# =============================================================================
def test_fast_path_throughput_burst():
    """Comprova alta vazão do Fast-Path executando 50 documentos em menos de 1000ms."""
    engine = FastPathEngine()
    t_start = time.perf_counter()

    for i in range(50):
        engine.process(SCENARIO_1_ROUTINE.documento_texto)

    duracao_total_ms = (time.perf_counter() - t_start) * 1000
    media_por_doc_ms = duracao_total_ms / 50

    assert duracao_total_ms < 1000.0, f"Burst de 50 requisições excedeu 1000ms: {duracao_total_ms:.1f}ms"
    assert media_por_doc_ms < 20.0, f"Tempo médio por documento excedeu 20ms: {media_por_doc_ms:.2f}ms"
