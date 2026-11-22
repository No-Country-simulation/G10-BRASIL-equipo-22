"""
Suíte de Testes Automatizados — Conformidade da Submissão Hackathon ONE G10
CARDs 43-48 / Issues #52-#57 — Sprint M6 (Equipo 22)

Valida que:
1. Todos os artefatos obrigatórios da Semana 6 existem em week6/.
2. O dump SQL week6/snapshot_db_avaliacao.sql possui sintaxe válida e dados populados.
3. O checklist week6/checklist_submissao_one.md está 100% aprovado ([x]).
4. O README.md possui os badges e links atualizados para a Release 1.5.0 Freeze.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent


def test_week6_artefatos_obrigatorios_existem() -> None:
    """Verifica que todos os artefatos de encerramento da Sprint M6 existem."""
    artefatos = [
        "week6/coverage_report_v1.5.txt",
        "week6/demo_runner.py",
        "week6/demo_output_sample.txt",
        "week6/roteiro_video_3min.md",
        "week6/demo_video_metadata.md",
        "week6/demo_oci_buckets.md",
        "week6/relatorio_executivo_oci.md",
        "week6/snapshot_db_avaliacao.sql",
        "week6/intro_video_contexto.md",
        "week6/checklist_submissao_one.md",
    ]
    
    for arq in artefatos:
        caminho = ROOT_DIR / arq
        assert caminho.exists(), f"Artefato essencial '{arq}' ausente!"
        assert caminho.stat().st_size > 0, f"Artefato '{arq}' está vazio!"


def test_snapshot_db_avaliacao_sql_valido() -> None:
    """Testa que o dump SQL do banco de auditoria pode ser restaurado em memória."""
    sql_path = ROOT_DIR / "week6" / "snapshot_db_avaliacao.sql"
    assert sql_path.exists(), "week6/snapshot_db_avaliacao.sql não encontrado!"
    
    dump_conteudo = sql_path.read_text(encoding="utf-8")
    assert "CREATE TABLE" in dump_conteudo
    assert "INSERT INTO" in dump_conteudo
    
    # Restaura o dump em uma base SQLite em memória para provar integridade
    mem_conn = sqlite3.connect(":memory:")
    mem_conn.executescript(dump_conteudo)
    cursor = mem_conn.cursor()
    
    # Verifica que as tabelas de auditoria foram restauradas com sucesso
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    assert "triagem_audit_log" in tables or "clinico_audit_historico" in tables
    
    mem_conn.close()


def test_checklist_submissao_totalmente_conforme() -> None:
    """Valida que todos os itens do checklist de submissão do ONE estão marcados como [x]."""
    checklist_path = ROOT_DIR / "week6" / "checklist_submissao_one.md"
    assert checklist_path.exists(), "week6/checklist_submissao_one.md não encontrado!"
    
    conteudo = checklist_path.read_text(encoding="utf-8")
    
    # Não deve haver nenhum item pendente [ ]
    assert "[ ]" not in conteudo, "Existem itens pendentes no checklist de submissão!"
    
    # Deve conter múltiplos itens concluídos [x]
    itens_concluidos = conteudo.count("[x]")
    assert itens_concluidos >= 10, f"Esperado ao menos 10 itens concluídos, encontrado {itens_concluidos}."


def test_readme_badges_e_submissao() -> None:
    """Valida integridade do README.md quanto a badges, release e instruções."""
    readme_path = ROOT_DIR / "README.md"
    assert readme_path.exists()
    
    conteudo = readme_path.read_text(encoding="utf-8")
    assert "Release-1.5.0" in conteudo
    assert "Pytest-180_Passed_100%25" in conteudo or "Pytest" in conteudo
    assert "sa-saopaulo-1" in conteudo or "Always Free" in conteudo
