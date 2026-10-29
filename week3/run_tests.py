#!/usr/bin/env python3
"""
MediFlow — Runner Executivo de Auto-Testes (Release 1.3)
Hackathon ONE G10 — Oracle Next Education & Alura (Equipo 22)

Este script executa toda a bateria de testes automatizados da Release 1.3
e renderiza um relatório executivo formatado para apresentação da squad na quinta-feira.

Uso:
    python week3/run_tests.py
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

# Ajuste de path para o projeto raiz
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import pytest


def main() -> int:
    border = "=" * 80
    sub_border = "-" * 80

    print(border)
    print(" 🏥 MEDIFLOW RELEASE 1.3 — BATERIA DE AUTO-TESTES AUTOMATIZADOS")
    print(" Hackathon ONE G10 (Oracle Next Education & Alura) — Equipo 22")
    print(border)
    print(" SQUAD & PERSONAS RESPONSÁVEIS:")
    print("  • Carlos Magno  (magnomct) : Tech Lead, SRE/DevOps, IA & Python Core")
    print("  • Fernando Szekut (FSzekut): Agent Integration, Webhooks & Front/UX")
    print("  • Helder (Atlas Data)      : OCI Object Storage Always Free & SQLite Audit")
    print("  • Alessandro (Marcus)      : Backend FastAPI, HitL Endpoints & QA")
    print(sub_border)
    print(" ARQUITETURA EM TESTE:")
    print("  1. LangGraph StateGraph (Ingestão -> Classificação -> Validação -> Router -> OCI)")
    print("  2. Webhook Dispatcher em Tempo Real (Alerta_Plantao_Medico)")
    print("  3. Segregação Dinâmica de Pastas OCI por Especialidade Médica")
    print("  4. Histórico Transacional de Auditoria em SQLite Local")
    print("  5. Telemetria SRE de Latência por Nó & Garantia de SLA < 5000ms")
    print("  6. Endpoints REST da API FastAPI v1.3 (Inspeção do Grafo, Triagem & HitL)")
    print(border)
    print("\nExecutando suite de testes automatizados com pytest...\n")

    test_file = str(Path(__file__).resolve().parent / "test_week3.py")
    t0 = time.time()
    exit_code = pytest.main(["-v", test_file, "--tb=short"])
    elapsed = time.time() - t0

    print("\n" + border)
    if exit_code == 0:
        print(" [OK] TODOS OS 8 TESTES FORAM APROVADOS COM SUCESSO!")
        print(f" Tempo Total de Execução: {elapsed:.2f} segundos")
        print(" Status da Release 1.3: PRONTA PARA HOMOLOGAÇÃO DA SQUAD NA QUINTA-FEIRA")
    else:
        print(f" [FALHA] Alguns testes falharam (Exit code: {exit_code}).")
        print(" Verifique o traceback acima para depuração.")
    print(border + "\n")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())

