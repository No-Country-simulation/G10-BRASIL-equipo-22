"""
Suíte de Testes Automatizados — Demonstração Técnica LangGraph + SRE
CARD-38 / Issue #47 — Sprint M6 (Hackathon ONE G10 - Equipo 22)

Valida que:
1. O script week6/demo_runner.py executa ponta-a-ponta via subprocess com código 0.
2. A saída contém as seções obrigatórias: 3 cenários clínicos, percentis SRE e Circuit-Breaker.
3. As funções do demo_runner podem ser executadas programaticamente com sucesso.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent


def test_demo_runner_subprocess_execution() -> None:
    """Executa week6/demo_runner.py e verifica integridade de saída e exit code 0."""
    script_path = ROOT_DIR / "week6" / "demo_runner.py"
    assert script_path.exists(), "week6/demo_runner.py deve existir!"
    
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
        timeout=30,
    )
    
    assert result.returncode == 0, f"demo_runner.py falhou com stderr:\n{result.stderr}"
    stdout = result.stdout
    
    # Validar presença dos 3 cenários clínicos
    assert "CENÁRIO 1 (ROTINA)" in stdout
    assert "CENÁRIO 2 (URGÊNCIA CRÍTICA TEP)" in stdout
    assert "CENÁRIO 3 (HITL AMBÍGUO)" in stdout
    
    # Validar seções de telemetria e SRE
    assert "TELEMETRIA SRE" in stdout
    assert "p50 (Mediana)" in stdout
    assert "p99" in stdout
    assert "SLA Compliance" in stdout
    
    # Validar máquina de estados do Circuit-Breaker
    assert "CIRCUIT-BREAKER" in stdout
    assert "CLOSED" in stdout
    assert "OPEN" in stdout
    assert "Zero Downtime" in stdout


def test_demo_runner_programmatic_api() -> None:
    """Invoca as funções de week6/demo_runner diretamente para asserções de tipos."""
    from week6.demo_runner import (
        run_langgraph_clinical_scenarios,
        run_sre_telemetry_demo,
        run_circuit_breaker_sre_demo,
    )
    
    resultados = run_langgraph_clinical_scenarios()
    assert len(resultados) == 3
    assert resultados[0]["prioridade"] == "Rotina"
    assert resultados[1]["prioridade"] == "Urgente"
    assert resultados[2]["requer_hitl"] is True
    
    latencias = [r["latencia_ms"] for r in resultados]
    metricas = run_sre_telemetry_demo(latencias)
    assert "p50" in metricas
    assert "p99" in metricas
    assert metricas["p99"] < 5000.0
    
    # Valida execução do Circuit-Breaker sem exceções
    run_circuit_breaker_sre_demo()
