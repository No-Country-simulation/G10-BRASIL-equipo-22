#!/usr/bin/env python3
"""
MediFlow — Runner Executivo de Auto-Testes e Carga Concorrente SRE (Release 1.4)
Hackathon ONE G10 — Oracle Next Education & Alura (Equipo 22)

Squad:
  - Carlos Magno  (magnomct) : Tech Lead, SRE/DevOps, IA & Python Core
  - Fernando Szekut (FSzekut): Agent Integration, Webhooks & Front/UX
  - Helder (Atlas Data)      : OCI Object Storage Always Free & SQLite Audit
  - Alessandro (Marcus)      : Backend FastAPI, HitL Endpoints & QA

Uso:
  python week4/run_week4_tests.py
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

# Ajuste de path para o projeto raiz
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import pytest
from week4.telemetry_sre import SRETelemetryEngine
from week4.load_testing import ConcurrentLoadTester


def main() -> int:
    border = "=" * 80
    sub_border = "-" * 80

    print(border)
    print(" 🏥 MEDIFLOW RELEASE 1.4 — CI/CD, TELEMETRIA SRE & CARGA CONCORRENTE")
    print(" Hackathon ONE G10 (Oracle Next Education & Alura) — Equipo 22")
    print(border)
    print(" SQUAD & PERSONAS RESPONSÁVEIS:")
    print("  • Carlos Magno  (magnomct) : Tech Lead, SRE/DevOps, IA & Python Core")
    print("  • Fernando Szekut (FSzekut): Agent Integration, Webhooks & Front/UX")
    print("  • Helder (Atlas Data)      : OCI Object Storage Always Free & SQLite Audit")
    print("  • Alessandro (Marcus)      : Backend FastAPI, HitL Endpoints & QA")
    print(sub_border)
    print(" ENTREGAS EM VALIDAÇÃO (SEMANA 4):")
    print("  1. Pipeline CI/CD GitHub Actions (.github/workflows/ci.yml)")
    print("  2. Motor de Telemetria de Produção SRE (Percentis p50/p95/p99 & Error Budget)")
    print("  3. Benchmark de Concorrência & Stress Burst (10, 25 e 50 requisições simultâneas)")
    print("  4. Endpoint REST /api/v1/telemetria/producao integrado ao FastAPI v1.4")
    print(border)

    print("\n⚡ [1/2] EXECUTANDO BENCHMARKS DE CARGA CONCORRENTE SRE...")
    tester = ConcurrentLoadTester()
    levels = [10, 25, 50]
    benchmark_results = []

    for lvl in levels:
        print(f"  -> Disparando carga concorrente com {lvl} admissões simultâneas...")
        res = tester.run_concurrency_test(concurrency=lvl)
        benchmark_results.append(res)

    print("\n📊 RESULTADOS DO BENCHMARK DE CONCORRÊNCIA:")
    print(f"{'Carga':<8} | {'Workers':<8} | {'Duração':<10} | {'Throughput':<14} | {'Lat. Média':<12} | {'p95':<10} | {'SLA (<5s)':<10}")
    print("-" * 80)
    for b in benchmark_results:
        dur = f"{b['tempo_total_segundos']}s"
        rps = f"{b['throughput_rps']} req/s"
        media = f"{b['latencia_media_ms']}ms"
        p95 = f"{b['p95_ms']}ms"
        sla = f"{b['cumprimento_sla_percentual']}%"
        print(f"{b['concorrencia_testada']:<8} | {b['workers_alocados']:<8} | {dur:<10} | {rps:<14} | {media:<12} | {p95:<10} | {sla:<10}")
    print("-" * 80)

    print("\n🛡️ [2/2] EXECUTANDO BATERIA DE AUTO-TESTES DA SEMANA 4 COM PYTEST...\n")
    test_file = str(Path(__file__).resolve().parent / "test_week4.py")
    t0 = time.time()
    exit_code = pytest.main(["-v", test_file, "--tb=short"])
    elapsed = time.time() - t0

    print("\n" + border)
    if exit_code == 0:
        print(" [OK] TODOS OS 8 TESTES DA SEMANA 4 FORAM APROVADOS COM SUCESSO!")
        print(f" Tempo de Execução dos Testes: {elapsed:.2f} segundos")
        print(" Status da Sprint M4: REQUISITOS SRE E CI/CD HOMOLOGADOS COM SUCESSO")
    else:
        print(f" [FALHA] Alguns testes falharam (Exit code: {exit_code}).")
    print(border + "\n")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
