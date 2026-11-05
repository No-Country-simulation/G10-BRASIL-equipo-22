"""
MediFlow — Suite de Auto-Testes da Semana 4 (Release 1.4)
Hackathon ONE G10 — Oracle Next Education & Alura (Equipo 22)

Squad:
  - Carlos Magno (Tech Lead, SRE/DevOps, IA & Python Core)
  - Fernando Szekut (Agent Integration, Webhooks & Frontend/UX)
  - Helder (Atlas Data — OCI Object Storage & SQLite Audit)
  - Alessandro (Marcus Builder — Backend FastAPI & QA)

Execução:
  pytest week4/test_week4.py -v
  python week4/run_week4_tests.py
"""

import json
import os
import sys
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Adiciona diretório raiz ao PYTHONPATH
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from week4.telemetry_sre import SRETelemetryEngine, SLA_MAX_LATENCY_MS, AVAILABILITY_TARGET
from week4.load_testing import ConcurrentLoadTester
from week3.api import app


# =============================================================================
# TESTE 1: Validação Estrutural e Sintática do Workflow CI/CD (GitHub Actions)
# =============================================================================
def test_ci_cd_workflow_syntax_and_structure():
    """Valida a existência, integridade sintática e passos do pipeline CI/CD."""
    ci_file = ROOT_DIR / ".github" / "workflows" / "ci.yml"
    if not ci_file.exists():
        ci_file = ROOT_DIR / "ci" / "ci.yml"
    assert ci_file.exists(), "O arquivo de workflow ci.yml deve existir."

    content = ci_file.read_text(encoding="utf-8")
    assert "name: MediFlow CI/CD Pipeline" in content
    assert "actions/checkout@v4" in content
    assert "actions/setup-python@v5" in content
    assert "python-version: '3.12'" in content
    assert "pip install -r requirements.txt" in content
    assert "pytest week3/test_week3.py" in content
    assert "pytest week4/test_week4.py" in content
    assert "python week4/run_week4_tests.py" in content


# =============================================================================
# TESTE 2: Cálculo Matemático Exato de Percentis SRE (p50, p75, p90, p95, p99)
# =============================================================================
def test_sre_telemetry_percentiles_calculation():
    """Valida o cálculo determinístico de percentis de latência pelo motor SRE."""
    # Amostra de 100 valores de 1.0 a 100.0 ms
    data = [float(i) for i in range(1, 101)]

    p50 = SRETelemetryEngine.calculate_percentile(data, 50.0)
    p75 = SRETelemetryEngine.calculate_percentile(data, 75.0)
    p90 = SRETelemetryEngine.calculate_percentile(data, 90.0)
    p95 = SRETelemetryEngine.calculate_percentile(data, 95.0)
    p99 = SRETelemetryEngine.calculate_percentile(data, 99.0)

    assert p50 == pytest.approx(50.5, 0.5)
    assert p75 == pytest.approx(75.25, 0.5)
    assert p90 == pytest.approx(90.1, 0.5)
    assert p95 == pytest.approx(95.05, 0.5)
    assert p99 == pytest.approx(99.01, 0.5)

    # Caso com lista vazia e unitária
    assert SRETelemetryEngine.calculate_percentile([], 50.0) == 0.0
    assert SRETelemetryEngine.calculate_percentile([42.0], 99.0) == 42.0


# =============================================================================
# TESTE 3: Cálculo do Error Budget e Respeito ao SLA de Latência (< 5000ms)
# =============================================================================
def test_sre_error_budget_and_sla_enforcement():
    """Valida o consumo de error budget e verificação de SLA sob contingências."""
    engine = SRETelemetryEngine()

    mock_records = [
        {"latencia_ms": 120.0, "status_final": "processado", "prioridade": "Rotina", "provedor_ia": "NVIDIA NIM"},
        {"latencia_ms": 250.0, "status_final": "processado", "prioridade": "Urgente", "provedor_ia": "NVIDIA NIM"},
        {"latencia_ms": 310.0, "status_final": "retido_auditoria_humana", "prioridade": "Revisao_Humana", "provedor_ia": "Heuristic SRE"},
        {"latencia_ms": 5200.0, "status_final": "processado", "prioridade": "Rotina", "provedor_ia": "Heuristic SRE"},  # Violou SLA
    ]

    metrics = engine.collect_metrics_from_records(mock_records)

    assert metrics["total_requisicoes"] == 4
    assert metrics["sla"]["requisicoes_em_sla"] == 3
    assert metrics["sla"]["taxa_cumprimento_sla_percentual"] == 75.0
    assert metrics["error_budget"]["status_resiliencia"] == "EXCELENTE (Budget Saudável)"
    assert metrics["distribuicao_provedor"]["NVIDIA NIM"] == 2
    assert metrics["distribuicao_provedor"]["Heuristic SRE"] == 2


# =============================================================================
# TESTE 4: Serialização e Exportação de Métricas em Arquivo JSON
# =============================================================================
def test_sre_telemetry_export_json():
    """Valida a exportação segura do arquivo telemetria_producao_sre.json."""
    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = Path(tmpdir) / "test_telemetria.json"
        engine = SRETelemetryEngine()
        exported = engine.export_metrics_json(output_path=json_path)

        assert exported.exists()
        content = json.loads(exported.read_text(encoding="utf-8"))
        assert "total_requisicoes" in content
        assert "latencias_ms" in content
        assert "sla" in content
        assert "error_budget" in content
        assert "timestamp_coleta" in content


# =============================================================================
# TESTE 5: Teste de Carga Concorrente com 10 Requisições Simultâneas
# =============================================================================
def test_concurrent_load_10_requests():
    """Valida a vazão concorrente com 10 admissões simultâneas de prontuários."""
    tester = ConcurrentLoadTester()
    res = tester.run_concurrency_test(concurrency=10, max_workers=4)

    assert res["concorrencia_testada"] == 10
    assert res["requisicoes_com_sucesso"] == 10
    assert res["requisicoes_com_falha"] == 0
    assert res["taxa_sucesso_percentual"] == 100.0
    assert res["cumprimento_sla_percentual"] == 100.0
    assert res["throughput_rps"] > 0.0


# =============================================================================
# TESTE 6: Teste de Carga Concorrente com 25 Requisições e Avaliação de Throughput
# =============================================================================
def test_concurrent_load_25_requests_throughput():
    """Valida o throughput sustentado (RPS) sob burst de 25 documentos hospitalares."""
    tester = ConcurrentLoadTester()
    res = tester.run_concurrency_test(concurrency=25, max_workers=8)

    assert res["concorrencia_testada"] == 25
    assert res["requisicoes_com_sucesso"] == 25
    assert res["taxa_sucesso_percentual"] == 100.0
    assert res["p95_ms"] < SLA_MAX_LATENCY_MS
    assert res["throughput_rps"] > 5.0  # Mínimo de 5 RPS sustentados


# =============================================================================
# TESTE 7: Teste de Stress Burst com 50 Requisições Concorrentes
# =============================================================================
def test_concurrent_load_50_stress_burst():
    """Testa a estabilidade sob carga extrema de 50 requisições simultâneas."""
    tester = ConcurrentLoadTester()
    res = tester.run_concurrency_test(concurrency=50, max_workers=12)

    assert res["concorrencia_testada"] == 50
    assert res["requisicoes_com_sucesso"] == 50
    assert res["requisicoes_com_falha"] == 0
    assert res["taxa_sucesso_percentual"] == 100.0
    assert res["cumprimento_sla_percentual"] == 100.0
    assert res["p99_ms"] < SLA_MAX_LATENCY_MS


# =============================================================================
# TESTE 8: Integração do Endpoint FastAPI GET /api/v1/telemetria/producao
# =============================================================================
def test_fastapi_week4_sre_telemetry_endpoint():
    """Valida a consulta das métricas avançadas SRE pela API REST v1.4."""
    client = TestClient(app)
    res = client.get("/api/v1/telemetria/producao")

    assert res.status_code == 200
    data = res.json()
    assert "total_requisicoes" in data
    assert "latencias_ms" in data
    assert "p50" in data["latencias_ms"]
    assert "p95" in data["latencias_ms"]
    assert "p99" in data["latencias_ms"]
    assert "sla" in data
    assert "error_budget" in data
