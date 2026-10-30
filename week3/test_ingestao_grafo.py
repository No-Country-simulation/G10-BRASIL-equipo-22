"""
MediFlow — Testes da Ingestão Multimodal dentro do Grafo (Release 1.3)
Hackathon ONE G10 — Oracle Next Education & Alura (Equipo 22)

O ingestor_node passa o anexo (arquivo_binario_b64) pelo mediflow_ingestao: a camada de texto
do PDF vira texto, página escaneada e foto viram JPEG para o modelo de visão. Documentos dos
casos sintéticos em dados_sinteticos/documentos/.

Execução:
  pytest week3/test_ingestao_grafo.py -v
"""

import base64
import io
import json
import sys
import tempfile
from pathlib import Path

import pytest
from PIL import Image
from pydantic import ValidationError

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import week3.agent as agent_module
from mediflow_schemas import DestinoRoteamentoEnum, DocumentoClinicoInput, TipoArquivoEnum
from week3.agent import MediFlowStateGraphAgent
from week3.notifications import NotificationDispatcher
from week3.storage import OCIStorageServiceV3

DOCUMENTOS = ROOT_DIR / "dados_sinteticos" / "documentos"
GABARITO = ROOT_DIR / "dados_sinteticos" / "gabarito"


def anexo(nome: str, tipo: TipoArquivoEnum) -> DocumentoClinicoInput:
    """Documento só com o arquivo, sem texto: como chega um scan ou uma foto."""
    dados = (DOCUMENTOS / nome).read_bytes()
    return DocumentoClinicoInput(
        documento_id=Path(nome).stem,
        tipo_arquivo=tipo,
        arquivo_binario_b64=base64.b64encode(dados).decode("ascii"),
    )


@pytest.fixture
def temp_workspace(monkeypatch):
    """Ambiente temporário isolado, como em test_week3.py, sempre no fallback heurístico."""
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = OCIStorageServiceV3(
            bucket_name="mediflow-test-bucket",
            local_fallback_dir=Path(tmpdir) / "oci_bucket",
            db_path=Path(tmpdir) / "test_audit.db",
        )
        dispatcher = NotificationDispatcher(mock_mode=True)
        agent = MediFlowStateGraphAgent(storage_service=storage, notification_dispatcher=dispatcher)
        yield {"agent": agent}


def ingerir_no_grafo(agent: MediFlowStateGraphAgent, documento: DocumentoClinicoInput) -> dict:
    return agent.ingestor_node({"documento_input": documento, "telemetria_sre": {}})


# =============================================================================
# Contrato de entrada
# =============================================================================
def test_contrato_aceita_so_arquivo_e_recusa_documento_vazio():
    DocumentoClinicoInput(documento_id="X1", arquivo_binario_b64="JVBERi0=")
    with pytest.raises(ValidationError, match="documento_texto, arquivo_binario_b64"):
        DocumentoClinicoInput(documento_id="X2")


# =============================================================================
# Ingestão: texto, foto e scan
# =============================================================================
def test_pdf_digital_vira_texto(temp_workspace):
    estado = ingerir_no_grafo(temp_workspace["agent"], anexo("SINT-012.pdf", TipoArquivoEnum.PDF))

    paciente = json.loads((GABARITO / "SINT-012.json").read_text(encoding="utf-8"))["dados_extraidos"]["paciente"]
    assert paciente["nome"] in estado["texto_normalizado"]
    assert estado["imagens_paginas"] == []
    assert estado["avisos_ingestao"] == []
    assert estado["telemetria_sre"]["modo_leitura"] == "texto"


def test_foto_vira_imagem_e_sem_modelo_vai_para_revisao(temp_workspace):
    documento = anexo("SINT-014.jpg", TipoArquivoEnum.IMAGEM)
    estado = ingerir_no_grafo(temp_workspace["agent"], documento)

    assert estado["texto_normalizado"] == ""
    assert len(estado["imagens_paginas"]) == 1
    assert estado["imagens_paginas"][0].startswith("data:image/jpeg;base64,")

    # Sem NVIDIA_API_KEY ninguém lê a imagem: nunca pode ir sozinho para a rotina
    resultado = temp_workspace["agent"].run(documento)
    assert resultado.decisao_roteamento.destino_principal == DestinoRoteamentoEnum.FILA_REVISAO_HUMANA


def test_scan_com_varias_paginas_avisa_que_o_modelo_ve_uma(temp_workspace):
    pagina = Image.new("RGB", (850, 1100), "white")
    pdf = io.BytesIO()
    pagina.save(pdf, "PDF", save_all=True, append_images=[pagina.copy()])
    documento = DocumentoClinicoInput(
        documento_id="DOC-SCAN-2-PAGINAS",
        arquivo_binario_b64=base64.b64encode(pdf.getvalue()).decode("ascii"),
    )

    estado = ingerir_no_grafo(temp_workspace["agent"], documento)
    assert len(estado["imagens_paginas"]) == 2
    assert any("recebe só a primeira" in aviso for aviso in estado["avisos_ingestao"])


def test_anexo_invalido_vai_para_revisao_com_o_motivo(temp_workspace):
    documento = DocumentoClinicoInput(documento_id="DOC-ANEXO-RUIM", arquivo_binario_b64="isto não é base64!")

    resultado = temp_workspace["agent"].run(documento)
    assert resultado.decisao_roteamento.destino_principal == DestinoRoteamentoEnum.FILA_REVISAO_HUMANA
    assert "anexo não pôde ser lido" in resultado.decisao_roteamento.justificativa_roteamento


# =============================================================================
# Chamada ao NIM: PDF escaneado chega como JPEG, uma imagem por requisição
# =============================================================================
class _RespostaFalsa:
    status_code = 200

    def json(self):
        conteudo = {
            "tipo_documento": "Laudo de Exame de Imagem",
            "especialidade": "Radiologia / Pneumologia",
            "nivel_prioridade": "Urgente",
            "score_confianca_classificacao": 0.95,
            "paciente": {"nome": None, "idade": None},
            "medico_solicitante": {"nome": "Dra. Teste", "crm": "12345-PR"},
            "diagnostico_principal": "Tromboembolismo Pulmonar Agudo",
            "cid_sugerido": "I26.9",
        }
        return {"choices": [{"message": {"content": json.dumps(conteudo)}}]}


def test_pdf_escaneado_vai_ao_nim_como_jpeg(temp_workspace, monkeypatch):
    requisicoes = []

    class ClienteFalso:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def post(self, url, **kwargs):
            requisicoes.append(kwargs["json"])
            return _RespostaFalsa()

    monkeypatch.setattr(agent_module.httpx, "Client", ClienteFalso)
    agent = temp_workspace["agent"]
    agent.nvidia_api_key = "chave-de-teste"

    agent.run(anexo("SINT-025.pdf", TipoArquivoEnum.PDF))

    assert len(requisicoes) == 1
    conteudo = requisicoes[0]["messages"][1]["content"]
    imagens = [parte for parte in conteudo if parte["type"] == "image_url"]
    assert len(imagens) == 1
    url = imagens[0]["image_url"]["url"]
    assert url.startswith("data:image/jpeg;base64,")
    assert base64.b64decode(url.split(",", 1)[1])[:3] == b"\xff\xd8\xff"  # JPEG, não os bytes do PDF
