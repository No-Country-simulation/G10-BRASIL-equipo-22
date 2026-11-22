"""
MediFlow — Testes de Persistência OCI ATP, Validação de Bucket e Política de Expurgo
Hackathon ONE G10 — Oracle Next Education & Alura (Equipo 22)
Sprint M4: CARD-19 (#28), CARD-20 (#29), CARD-21 (#30)
"""

import json
import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from oci_storage import OCIATPManager, OCIStorageService


@pytest.fixture
def tmp_db(tmp_path):
    db_file = tmp_path / "test_audit.db"
    return str(db_file)


@pytest.fixture
def oci_service(tmp_path):
    return OCIStorageService(local_fallback_dir=tmp_path / "oci_local")


# =============================================================================
# CARD-19 (#28) — OCI Autonomous Database (ATP Always Free) com JSON
# =============================================================================

def test_atp_manager_ddl_and_init(tmp_db):
    """Valida DDL e inicialização das tabelas de auditoria clínica."""
    manager = OCIATPManager(db_path=tmp_db)
    assert "CHECK (payload_json IS JSON)" in manager.DDL_ORACLE_ATP
    assert "clinico_audit_historico" in manager.DDL_SQLITE_COMPAT


def test_atp_manager_salvar_e_consultar_crm(tmp_db):
    """Valida inserção e consulta relacional com coluna JSON."""
    manager = OCIATPManager(db_path=tmp_db)
    payload = {
        "paciente": "Carlos Andrade",
        "medicamentos": ["Aspirina 100mg", "Atorvastatina 40mg"],
        "especialidade": "Cardiologia",
    }
    sucesso = manager.salvar_registro(
        documento_id="DOC-ATP-001",
        tipo_documento="Receituário Médico",
        crm_medico="CRM-SP 12345",
        paciente_nome="Carlos Andrade",
        prioridade="Rotina",
        score_confianca=0.98,
        requer_auditoria=False,
        payload_json=payload,
    )
    assert sucesso is True

    registros = manager.consultar_por_crm("CRM-SP 12345")
    assert len(registros) == 1
    reg = registros[0]
    assert reg["documento_id"] == "DOC-ATP-001"
    assert reg["paciente_nome"] == "Carlos Andrade"
    assert reg["payload"]["medicamentos"] == ["Aspirina 100mg", "Atorvastatina 40mg"]


def test_atp_manager_consultar_urgencias(tmp_db):
    """Valida filtro específico para casos de urgência hospitalar."""
    manager = OCIATPManager(db_path=tmp_db)
    manager.salvar_registro(
        documento_id="DOC-URG-001",
        tipo_documento="Laudo de Exame",
        crm_medico="CRM-SP 55555",
        paciente_nome="Ana Clara",
        prioridade="Urgente",
        score_confianca=0.99,
        requer_auditoria=False,
        payload_json={"diagnostico": "TEP Agudo"},
    )
    manager.salvar_registro(
        documento_id="DOC-ROT-002",
        tipo_documento="Receita",
        crm_medico="CRM-SP 55555",
        paciente_nome="Pedro Lucas",
        prioridade="Rotina",
        score_confianca=0.95,
        requer_auditoria=False,
        payload_json={"diagnostico": "Rinite"},
    )

    urgentes = manager.consultar_urgencias()
    assert len(urgentes) == 1
    assert urgentes[0]["documento_id"] == "DOC-URG-001"


# =============================================================================
# CARD-20 (#29) — Validação de Uploads com OCI SDK (head_object)
# =============================================================================

def test_validate_remote_upload_fallback_local(oci_service):
    """Testa validação de upload e cálculo de checksum no fallback local."""
    caminho = "processados/rotina/DOC-TEST-001.json"
    oci_service.save_json_object(caminho, {"teste": "validação"})

    resultado = oci_service.validate_remote_upload(caminho)
    assert resultado["valido"] is True
    assert resultado["caminho_objeto"] == caminho
    assert resultado["tamanho_bytes"] > 0
    assert resultado["etag"].startswith('"')


def test_validate_remote_upload_mock_oci_sdk(oci_service):
    """Testa validação simulando resposta do ObjectStorageClient.head_object."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.headers = {
        "etag": '"a1b2c3d4e5f6"',
        "content-length": "512",
        "content-type": "application/json",
    }
    mock_client.head_object.return_value = mock_response

    oci_service._oci_client = mock_client
    oci_service.namespace = "test_namespace"

    resultado = oci_service.validate_remote_upload("processados/urgentes/DOC-MOCK-001.json")
    assert resultado["valido"] is True
    assert resultado["modo"] == "oci_remoto"
    assert resultado["etag"] == '"a1b2c3d4e5f6"'
    assert resultado["tamanho_bytes"] == 512
    mock_client.head_object.assert_called_once()


# =============================================================================
# CARD-21 (#30) — Política de Expurgo e Retenção de 30 Dias
# =============================================================================

def test_regra_lifecycle_expurgo_30_dias():
    """Valida especificação da regra JSON de Lifecycle para o OCI Object Storage."""
    regra = OCIStorageService.obter_regra_lifecycle_expurgo_30_dias()
    assert regra["action"] == "DELETE"
    assert regra["timeAmount"] == 30
    assert regra["timeUnit"] == "DAYS"
    assert "recebidos/" in regra["objectNameFilter"]["inclusionPrefixes"]
    assert regra["isEnabled"] is True


def test_executar_politica_expurgo_local(oci_service):
    """Valida expurgo preventivo local de documentos brutos expirados."""
    caminho_antigo = "recebidos/DOC-ANTIGO.json"
    caminho_novo = "recebidos/DOC-NOVO.json"

    oci_service.save_json_object(caminho_antigo, {"idade": "antigo"})
    oci_service.save_json_object(caminho_novo, {"idade": "novo"})

    # Força data de modificação antiga no arquivo antigo (ex: 35 dias atrás)
    arquivo_antigo = oci_service.local_fallback_dir / oci_service.bucket_name / caminho_antigo
    tempo_35_dias_atras = time.time() - (35 * 86400)
    import os
    os.utime(arquivo_antigo, (tempo_35_dias_atras, tempo_35_dias_atras))

    # Executa com dry_run=True primeiro
    res_dry = oci_service.executar_politica_expurgo_30_dias(prefix="recebidos/", dias_retencao=30, dry_run=True)
    assert res_dry["objetos_expurgados_count"] == 1
    assert arquivo_antigo.exists()  # Não deve deletar em dry_run

    # Executa expurgo real
    res_real = oci_service.executar_politica_expurgo_30_dias(prefix="recebidos/", dias_retencao=30, dry_run=False)
    assert res_real["objetos_expurgados_count"] == 1
    assert not arquivo_antigo.exists()  # Deletado!

    # Arquivo novo deve permanecer intacto
    arquivo_novo = oci_service.local_fallback_dir / oci_service.bucket_name / caminho_novo
    assert arquivo_novo.exists()
