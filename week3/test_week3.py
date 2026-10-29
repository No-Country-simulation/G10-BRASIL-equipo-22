"""
MediFlow — Suite de Auto-Testes Automatizados (Release 1.3)
Hackathon ONE G10 — Oracle Next Education & Alura (Equipo 22)
Squad:
  - Carlos Magno (Tech Lead, SRE/DevOps, IA & Python Core)
  - Fernando Szekut (Agent Integration, Webhooks & UX)
  - Helder (Atlas Data — OCI Object Storage & SQLite Audit)
  - Alessandro (Marcus Builder — Backend FastAPI & QA)

Execução:
  pytest week3/test_week3.py -v
  python week3/run_tests.py
"""

import os
import sys
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Adiciona diretório raiz ao PYTHONPATH
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from mediflow_schemas import (
    DocumentoClinicoInput,
    DestinoRoteamentoEnum,
    NivelPrioridadeEnum,
    TipoArquivoEnum,
)
from week3.agent import (
    MediFlowStateGraphAgent,
    SCENARIO_1_ROUTINE,
    SCENARIO_2_URGENCY_TEP,
    SCENARIO_3_AMBIGUOUS_HITL,
)
from week3.notifications import NotificationDispatcher
from week3.storage import OCIStorageServiceV3
from week3.api import app


@pytest.fixture
def temp_workspace():
    """Cria um ambiente temporário isolado para testes de storage e banco SQLite."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_dir = Path(tmpdir) / "oci_bucket"
        db_path = Path(tmpdir) / "test_audit.db"
        storage = OCIStorageServiceV3(
            bucket_name="mediflow-test-bucket",
            local_fallback_dir=storage_dir,
            db_path=db_path,
        )
        dispatcher = NotificationDispatcher(mock_mode=True)
        agent = MediFlowStateGraphAgent(
            storage_service=storage,
            notification_dispatcher=dispatcher,
        )
        yield {
            "tmpdir": tmpdir,
            "storage": storage,
            "dispatcher": dispatcher,
            "agent": agent,
            "db_path": db_path,
        }


# =============================================================================
# TESTE 1: Cenário 1 — Fluxo Padrão de Rotina (Receita / Farmácia)
# =============================================================================
def test_langgraph_scenario_1_routine(temp_workspace):
    """
    Valida a triagem de rotina ambulatorial via StateGraph:
    - Score >= 0.85
    - Destino: Farmacia_Hospitalar
    - Requer Auditoria Humana: False
    - Segregação dinâmica de pasta: processados/rotina/{especialidade}/{id}.json
    """
    agent = temp_workspace["agent"]
    resultado = agent.run(SCENARIO_1_ROUTINE)

    assert resultado.status == "processado"
    assert resultado.documento_id == "DOC-CLIN-2026-1001"
    assert resultado.classificacao.tipo_documento == "Receituário Médico"
    assert resultado.classificacao.nivel_prioridade == NivelPrioridadeEnum.ROTINA
    assert resultado.classificacao.score_confianca_classificacao >= 0.85

    # Roteamento
    assert resultado.decisao_roteamento.destino_principal == DestinoRoteamentoEnum.FARMACIA_HOSPITALAR
    assert resultado.decisao_roteamento.requer_auditoria_humana is False

    # Entidades extraídas
    assert resultado.dados_extraidos.paciente.nome == "Mariana Costa Souza"
    assert resultado.dados_extraidos.medico_solicitante.crm == "198432-SP"
    assert resultado.dados_extraidos.medicamentos_prescritos is not None
    assert len(resultado.dados_extraidos.medicamentos_prescritos) > 0

    # Segregação dinâmica OCI
    caminho = resultado.armazenamento_oci.caminho_objeto
    assert caminho.startswith("processados/rotina/")
    assert caminho.endswith("DOC-CLIN-2026-1001.json")
    assert "clinica_medica" in caminho


# =============================================================================
# TESTE 2: Cenário 2 — Urgência Médica Crítica (TEP Agudo / Webhook)
# =============================================================================
def test_langgraph_scenario_2_urgency_tep(temp_workspace):
    """
    Valida o fluxo de urgência médica com ativação de Webhook:
    - Achado Crítico: TEP Agudo
    - Prioridade: Urgente
    - Destino: Fila_Emergencia_Medica
    - Disparo de Webhook para Alerta_Plantao_Medico (Fernando Szekut)
    - Segregação OCI: processados/urgentes/radiologia/...
    """
    agent = temp_workspace["agent"]
    dispatcher = temp_workspace["dispatcher"]
    resultado = agent.run(SCENARIO_2_URGENCY_TEP)

    assert resultado.status == "processado"
    assert resultado.documento_id == "DOC-CLIN-2026-8942"
    assert resultado.classificacao.nivel_prioridade == NivelPrioridadeEnum.URGENTE
    assert resultado.classificacao.score_confianca_classificacao >= 0.85

    # Roteamento de emergência
    assert resultado.decisao_roteamento.destino_principal == DestinoRoteamentoEnum.FILA_EMERGENCIA_MEDICA
    assert resultado.decisao_roteamento.requer_auditoria_humana is False
    assert resultado.decisao_roteamento.notificacao_gerada is not None
    assert resultado.decisao_roteamento.notificacao_gerada.canal == "Alerta_Plantao_Medico"

    # Confirmação no Dispatcher de Notificações
    alertas = dispatcher.historico_alertas
    assert len(alertas) >= 1
    ultimo_alerta = alertas[-1]
    assert ultimo_alerta.documento_id == "DOC-CLIN-2026-8942"
    assert "Carlos Eduardo Mendes" in ultimo_alerta.paciente_nome
    assert "Tromboembolismo Pulmonar Agudo" in ultimo_alerta.diagnostico

    # Segregação dinâmica OCI
    caminho = resultado.armazenamento_oci.caminho_objeto
    assert caminho.startswith("processados/urgentes/")
    assert "radiologia" in caminho


# =============================================================================
# TESTE 3: Cenário 3 — Caso Ambíguo / Rasura (Human-in-the-Loop)
# =============================================================================
def test_langgraph_scenario_3_ambiguous_hitl(temp_workspace):
    """
    Valida a retenção regulatória de documentos para Auditoria Humana (HitL):
    - CRM ausente e rasura no texto
    - Score < 0.85 (Threshold de segurança)
    - Destino: Fila_Revisao_Humana
    - Requer Auditoria Humana: True
    - Segregação OCI: auditoria_humana/{id}.json
    """
    agent = temp_workspace["agent"]
    resultado = agent.run(SCENARIO_3_AMBIGUOUS_HITL)

    assert resultado.status == "retido_auditoria_humana"
    assert resultado.documento_id == "DOC-CLIN-2026-5503"
    assert resultado.classificacao.nivel_prioridade == NivelPrioridadeEnum.REVISAO_HUMANA
    assert resultado.classificacao.score_confianca_classificacao < 0.85

    # Roteamento HitL
    assert resultado.decisao_roteamento.destino_principal == DestinoRoteamentoEnum.FILA_REVISAO_HUMANA
    assert resultado.decisao_roteamento.requer_auditoria_humana is True
    assert resultado.decisao_roteamento.notificacao_gerada is not None
    assert resultado.decisao_roteamento.notificacao_gerada.canal == "Painel_Auditoria_HitL"

    # Caminho OCI
    caminho = resultado.armazenamento_oci.caminho_objeto
    assert caminho.startswith("auditoria_humana/")
    assert caminho.endswith("DOC-CLIN-2026-5503.json")


# =============================================================================
# TESTE 4: Dispatcher de Notificações & Webhooks em Tempo Real
# =============================================================================
def test_webhook_dispatcher_mock():
    """Valida o despachador de notificações em modo mock."""
    dispatcher = NotificationDispatcher(mock_mode=True)
    res = dispatcher.dispatch_emergency_alert(
        documento_id="DOC-TEST-9999",
        paciente_nome="Ana Clara Santos",
        diagnostico="Infarto Agudo do Miocárdio (IAM)",
        crm_solicitante="999888-SP",
        canal="Alerta_Plantao_Medico",
    )

    assert res["status_envio"] == "sucesso_mock"
    assert res["payload"]["documento_id"] == "DOC-TEST-9999"
    assert res["payload"]["prioridade"] == "Urgente"
    assert res["payload"]["diagnostico"] == "Infarto Agudo do Miocárdio (IAM)"

    recentes = dispatcher.get_recent_alerts(limit=5)
    assert len(recentes) == 1
    assert recentes[0]["documento_id"] == "DOC-TEST-9999"


# =============================================================================
# TESTE 5: Segregação Dinâmica de Pastas OCI por Especialidade Médica
# =============================================================================
def test_oci_dynamic_specialty_paths(temp_workspace):
    """Valida a resolução de slugs e hierarquia de pastas dinâmicas do OCI."""
    storage = temp_workspace["storage"]

    # 1. Rotina com especialidade acentuada e composta
    path_rotina = storage.resolve_object_path(
        documento_id="DOC-101",
        requer_auditoria_humana=False,
        nivel_prioridade="Rotina",
        especialidade="Clínica Médica / Ambulatorial",
    )
    assert path_rotina == "processados/rotina/clinica_medica_ambulatorial/DOC-101.json"

    # 2. Urgência com especialidade Radiologia
    path_urgente = storage.resolve_object_path(
        documento_id="DOC-102",
        requer_auditoria_humana=False,
        nivel_prioridade="Urgente",
        especialidade="Radiologia",
    )
    assert path_urgente == "processados/urgentes/radiologia/DOC-102.json"

    # 3. HitL sem especialidade informada (revisão)
    path_hitl = storage.resolve_object_path(
        documento_id="DOC-103",
        requer_auditoria_humana=True,
        nivel_prioridade="Revisao_Humana",
        especialidade=None,
    )
    assert path_hitl == "auditoria_humana/geral/DOC-103.json"


# =============================================================================
# TESTE 6: Histórico Transacional SQLite (Atlas Data / Helder)
# =============================================================================
def test_sqlite_transactional_audit_log(temp_workspace):
    """Valida gravação, consulta e atualização transacional no SQLite."""
    storage = temp_workspace["storage"]

    # Gravar decisão
    storage.log_triage_decision(
        documento_id="DOC-SQL-001",
        tipo_documento="Receituário Médico",
        especialidade="Cardiologia",
        prioridade="Rotina",
        score_confianca=0.92,
        paciente_nome="Pedro Silva",
        medico_crm="123456-SP",
        diagnostico_principal="Hipertensão Arterial Sistêmica",
        destino_principal="Farmacia_Hospitalar",
        requer_auditoria=False,
        caminho_oci="processados/rotina/cardiologia/DOC-SQL-001.json",
        provedor_ia="NVIDIA NIM (Llama 3.2)",
        status_final="processado",
        latencia_ms=120.5,
    )

    # Consultar histórico
    historico = storage.get_audit_history(limit=10)
    assert len(historico) >= 1
    doc = next(d for d in historico if d["documento_id"] == "DOC-SQL-001")
    assert doc["paciente_nome"] == "Pedro Silva"
    assert doc["especialidade"] == "Cardiologia"
    assert doc["requer_auditoria"] == 0

    # Atualizar status após intervenção de auditoria
    storage.update_audit_status(
        documento_id="DOC-SQL-001",
        novo_status="aprovado_pos_auditoria",
        crm_corrigido="123456-SP-VALIDADO",
        novo_destino="Dispensacao_Imediata",
    )

    historico_atualizado = storage.get_audit_history(limit=10)
    doc_atualizado = next(d for d in historico_atualizado if d["documento_id"] == "DOC-SQL-001")
    assert doc_atualizado["status_final"] == "aprovado_pos_auditoria"
    assert doc_atualizado["medico_crm"] == "123456-SP-VALIDADO"
    assert doc_atualizado["destino_principal"] == "Dispensacao_Imediata"


# =============================================================================
# TESTE 7: Telemetria SRE & Verificação de SLA (Carlos Magno)
# =============================================================================
def test_sre_sla_and_telemetry(temp_workspace):
    """Valida as métricas de tempo de resposta SRE e enforcement do SLA < 5000ms."""
    agent = temp_workspace["agent"]
    storage = temp_workspace["storage"]

    # Executa triagem
    agent.run(SCENARIO_1_ROUTINE)

    compliance = storage.check_always_free_compliance()
    assert "Always Free" in compliance["tier"]
    assert "CONFORME" in compliance["compliance_status"]

    historico = storage.get_audit_history(limit=1)
    assert len(historico) > 0
    registro = historico[0]
    assert registro["latencia_ms"] is not None
    assert registro["latencia_ms"] < 5000.0  # SLA < 5 segundos


# =============================================================================
# TESTE 8: Endpoints da API REST FastAPI (Marcus Builder / Alessandro)
# =============================================================================
def test_fastapi_endpoints_v3():
    """Valida todos os endpoints REST da Release 1.3 via TestClient."""
    client = TestClient(app)

    # 0. Painel Web Oficial (Dashboard HTML na rota raiz)
    res_index = client.get("/")
    assert res_index.status_code == 200
    assert "MediFlow" in res_index.text
    assert "LangGraph" in res_index.text

    # 1. Healthcheck
    res_health = client.get("/health")
    assert res_health.status_code == 200
    data_health = res_health.json()
    assert data_health["status"] == "healthy"
    assert data_health["version"] == "1.3.0"
    assert "LangGraph StateGraph" in data_health["orchestration"]

    # 2. Estrutura do Grafo LangGraph
    res_graph = client.get("/api/v1/grafo/estrutura")
    assert res_graph.status_code == 200
    data_graph = res_graph.json()
    assert "ingestor" in data_graph["nos"]
    assert "emergency_route" in data_graph["nos"]
    assert "flowchart TD" in data_graph["mermaid_diagram"]

    # 3. Triagem de documento ambíguo (retem na fila HitL)
    payload = SCENARIO_3_AMBIGUOUS_HITL.to_dict()
    res_triagem = client.post("/api/v1/triagem", json=payload)
    assert res_triagem.status_code == 200
    data_triagem = res_triagem.json()
    assert data_triagem["status"] == "retido_auditoria_humana"
    doc_id = data_triagem["documento_id"]

    # 4. Listar fila de auditoria
    res_auditoria = client.get("/api/v1/auditoria")
    assert res_auditoria.status_code == 200
    fila = res_auditoria.json()
    assert any(item["documento_id"] == doc_id for item in fila)

    # 5. Aprovação do auditor médico com CRM corrigido
    res_aprovar = client.post(
        f"/api/v1/auditoria/{doc_id}/aprovar",
        params={"crm_corrigido": "184930-SP", "destino_final": "Farmacia_Hospitalar"},
    )
    assert res_aprovar.status_code == 200
    data_aprovado = res_aprovar.json()
    assert data_aprovado["status"] == "sucesso"
    assert data_aprovado["documento_atualizado"]["status"] == "aprovado_pos_auditoria"

    # 6. Telemetria SRE
    res_telemetria = client.get("/api/v1/telemetria")
    assert res_telemetria.status_code == 200
    data_telemetria = res_telemetria.json()
    assert "latencia_media_ms" in data_telemetria
    assert data_telemetria["sla_limite_ms"] == 5000.0

    # 7. Compliance OCI
    res_compliance = client.get("/api/v1/compliance/oci")
    assert res_compliance.status_code == 200
    assert "Always Free" in res_compliance.json()["tier"]
