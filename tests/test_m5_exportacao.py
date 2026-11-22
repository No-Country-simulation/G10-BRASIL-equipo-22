"""
MediFlow — Testes de Exportação de Dados Clínicos e Auditoria FinOps OCI
Hackathon ONE G10 — Oracle Next Education & Alura (Equipo 22)
Sprint M5: CARD-31 (#40), CARD-32 (#41), CARD-33 (#42)
"""

import json
from pathlib import Path
import pytest

from oci_storage import OCIATPManager
from week5.exportacao import exportar_prontuarios_csv, exportar_prontuarios_json
from week5.auditoria_orcamento_oci import auditar_conformidade_always_free, gerar_relatorio_texto


@pytest.fixture
def db_com_dados(tmp_path):
    db_file = tmp_path / "test_export.db"
    manager = OCIATPManager(db_path=str(db_file))
    manager.salvar_registro(
        documento_id="DOC-EXP-001",
        tipo_documento="Receituário Médico",
        crm_medico="CRM-SP 12345",
        paciente_nome="Mariana Lima",
        prioridade="Rotina",
        score_confianca=0.95,
        requer_auditoria=False,
        payload_json={"dados_extraidos": {"diagnostico_principal": "Hipertensão", "cid_sugerido": "I10"}},
    )
    manager.salvar_registro(
        documento_id="DOC-EXP-002",
        tipo_documento="Laudo de Exame",
        crm_medico="CRM-RJ 99999",
        paciente_nome="Gabriel Rocha",
        prioridade="Urgente",
        score_confianca=0.99,
        requer_auditoria=True,
        payload_json={"dados_extraidos": {"diagnostico_principal": "Pneumotórax", "cid_sugerido": "J93.9"}},
    )
    return str(db_file)


# =============================================================================
# CARD-32 (#41) — Exportação de Prontuários em CSV e JSON
# =============================================================================

def test_exportar_prontuarios_csv(db_com_dados, tmp_path):
    """Valida exportação em CSV com delimitadores e campos corretos."""
    csv_out = tmp_path / "prontuarios.csv"
    total = exportar_prontuarios_csv(str(csv_out), db_path=db_com_dados)
    assert total == 2
    assert csv_out.exists()
    conteudo = csv_out.read_text(encoding="utf-8")
    assert "DOC-EXP-001" in conteudo
    assert "Mariana Lima" in conteudo
    assert "Hipertensão" in conteudo


def test_exportar_prontuarios_csv_filtro_crm(db_com_dados, tmp_path):
    """Valida filtro por CRM na exportação CSV."""
    csv_out = tmp_path / "prontuarios_crm.csv"
    total = exportar_prontuarios_csv(str(csv_out), db_path=db_com_dados, crm="CRM-SP 12345")
    assert total == 1
    conteudo = csv_out.read_text(encoding="utf-8")
    assert "Mariana Lima" in conteudo
    assert "Gabriel Rocha" not in conteudo


def test_exportar_prontuarios_json(db_com_dados, tmp_path):
    """Valida exportação em JSON com metadados de sistema e lista de prontuários."""
    json_out = tmp_path / "prontuarios.json"
    total = exportar_prontuarios_json(str(json_out), db_path=db_com_dados)
    assert total == 2
    assert json_out.exists()
    dados = json.loads(json_out.read_text(encoding="utf-8"))
    assert dados["total_registros"] == 2
    assert len(dados["prontuarios"]) == 2
    assert dados["prontuarios"][0]["documento_id"] in ("DOC-EXP-001", "DOC-EXP-002")


# =============================================================================
# CARD-33 (#42) — Auditoria FinOps OCI comprovando R$ 0,00
# =============================================================================

def test_auditoria_orcamento_oci_custo_zero():
    """Valida cumprimento dos requisitos de gratuidade da camada Always Free."""
    auditoria = auditar_conformidade_always_free()
    assert auditoria["custo_total_faturado_brl"] == "R$ 0,00"
    assert "100% CONFORME" in auditoria["status_geral"]
    assert len(auditoria["itens"]) >= 3


def test_gerar_relatorio_texto_conformidade(tmp_path):
    """Valida geração do relatório textual de evidência para a banca avaliadora."""
    relatorio_path = tmp_path / "relatorio_finops.txt"
    texto = gerar_relatorio_texto(output_file=str(relatorio_path))
    assert relatorio_path.exists()
    assert "R$ 0,00" in texto
    assert "CONFORME" in texto
    assert "Always Free" in texto
