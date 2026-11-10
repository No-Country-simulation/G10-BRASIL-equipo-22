"""Testes da ingestão: os 25 documentos sintéticos e os casos de borda de um upload real."""
import csv
import io
import json
from pathlib import Path

import pypdfium2 as pdfium
import pytest
from PIL import Image

import mediflow_ingestao as ing

DADOS = Path(__file__).resolve().parent.parent / "dados_sinteticos"
with open(DADOS / "manifesto.csv", encoding="utf-8") as arquivo:
    MANIFESTO = list(csv.DictReader(arquivo))
MODO_ESPERADO = {"texto": "texto", "pdf_digital": "texto", "pdf_escaneado": "visao", "imagem": "visao"}


def gabarito(documento_id):
    return json.loads((DADOS / "gabarito" / f"{documento_id}.json").read_text(encoding="utf-8"))


def pdf_juntando(*caminhos):
    novo = pdfium.PdfDocument.new()
    for caminho in caminhos:
        novo.import_pages(pdfium.PdfDocument(str(caminho)))
    saida = io.BytesIO()
    novo.save(saida)
    return saida.getvalue()


def jpeg(largura, altura, orientacao=None):
    imagem = Image.new("RGB", (largura, altura), "white")
    exif = imagem.getexif()
    if orientacao:
        exif[0x0112] = orientacao
    saida = io.BytesIO()
    imagem.save(saida, "JPEG", exif=exif)
    return saida.getvalue()


# --- Os 25 documentos sintéticos -------------------------------------------------------------

@pytest.mark.parametrize("linha", MANIFESTO, ids=lambda linha: linha["documento_id"])
def test_documento_sintetico(linha):
    doc = ing.ingerir(DADOS / linha["arquivo"], canal_origem=linha["canal_origem"])

    assert doc.tipo_arquivo == linha["tipo_arquivo"]
    assert doc.modo_leitura == MODO_ESPERADO[linha["formato"]]
    assert doc.canal_origem == linha["canal_origem"]
    if doc.modo_leitura == "texto":
        dados = gabarito(linha["documento_id"])["dados_extraidos"]
        assert (dados["paciente"]["nome"] or dados["medico_solicitante"]["nome"]) in doc.documento_texto
    else:
        assert doc.documento_texto is None
        for pagina in doc.paginas:
            assert pagina.data_url().startswith("data:image/jpeg;base64,")
            assert max(pagina.largura, pagina.altura) <= ing.LADO_MAXIMO


def test_json_mantem_o_id_do_contrato():
    doc = ing.ingerir(DADOS / "documentos" / "SINT-011.json")
    assert doc.documento_id == "SINT-011"
    assert doc.canal_origem == "Pronto_Socorro"
    assert doc.para_contrato()["documento_texto"].startswith("Hospital Aurora do Vale")


def test_so_o_scan_ruim_gera_aviso_de_qualidade():
    com_aviso = []
    for linha in MANIFESTO:
        if linha["formato"] in ("pdf_escaneado", "imagem"):
            doc = ing.ingerir(DADOS / linha["arquivo"])
            if any("revisão humana" in aviso for aviso in doc.avisos):
                com_aviso.append(linha["documento_id"])
    assert com_aviso == ["SINT-022"]


# --- Casos de borda --------------------------------------------------------------------------

def test_foto_deitada_e_endireitada_pelo_exif():
    doc = ing.ingerir(jpeg(800, 600, orientacao=6))  # celular na vertical, gravado deitado
    assert (doc.paginas[0].largura, doc.paginas[0].altura) == (600, 800)


def test_imagem_grande_e_reduzida():
    doc = ing.ingerir(jpeg(4000, 3000))
    assert max(doc.paginas[0].largura, doc.paginas[0].altura) == ing.LADO_MAXIMO


def test_imagem_pequena_gera_aviso():
    doc = ing.ingerir(jpeg(400, 300))
    assert any("resolução baixa" in aviso for aviso in doc.avisos)


def test_pdf_misto_texto_e_escaneado():
    dados = pdf_juntando(DADOS / "documentos" / "SINT-001.pdf", DADOS / "documentos" / "SINT-004.pdf")
    doc = ing.ingerir(dados)
    assert doc.modo_leitura == "misto"
    assert [p.origem for p in doc.paginas] == ["camada_texto", "pdf_renderizado"]
    assert "José Aparecido Ramos" in doc.documento_texto


def test_pdf_longo_le_so_as_primeiras_paginas():
    dados = pdf_juntando(*[DADOS / "documentos" / "SINT-001.pdf"] * (ing.MAX_PAGINAS + 2))
    doc = ing.ingerir(dados)
    assert len(doc.paginas) == ing.MAX_PAGINAS
    assert any("primeiras foram lidas" in aviso for aviso in doc.avisos)


def test_extensao_nao_engana():
    dados = (DADOS / "documentos" / "SINT-001.pdf").read_bytes()
    assert ing.ingerir(dados, nome_arquivo="foto.jpg").tipo_arquivo == "PDF"


def test_texto_simples_e_normalizado():
    doc = ing.ingerir("Paciente:   Fulano\r\n\r\n\r\n\r\nCRM-PR 12345­ ".encode("utf-8"))
    assert doc.documento_texto == "Paciente: Fulano\n\nCRM-PR 12345"
    assert doc.modo_leitura == "texto"


def test_mesmo_arquivo_mesmo_id():
    dados = (DADOS / "documentos" / "SINT-009.jpg").read_bytes()
    assert ing.ingerir(dados).documento_id == ing.ingerir(dados).documento_id


def test_resumo_nao_carrega_imagens():
    resumo = ing.ingerir(DADOS / "documentos" / "SINT-014.jpg").resumo()
    assert "imagem_base64" not in resumo["paginas"][0]
    assert len(json.dumps(resumo)) < 2000


@pytest.mark.parametrize("dados, trecho", [
    (b"", "vazio"),
    (b"%PDF-1.7 isto nao e um pdf", "PDF corrompido"),
    (b"PK\x03\x04\x14\x00\x06\x00conteudo de um docx", "binário"),
    (bytes(range(128, 256)), "formato não suportado"),
    (b"\xff\xd8\xff\xe0 jpeg truncado", "imagem corrompida"),
    (b'{"documento_id": "X1", "documento_texto": "   "}', "documento_texto"),
    (b'{"documento_id": "X1", "documento_texto": "laudo"', "JSON"),
    (b"   \n\t  ", "sem conteúdo"),
])
def test_entrada_invalida(dados, trecho):
    with pytest.raises(ing.EntradaInvalida, match=trecho):
        ing.ingerir(dados)


def test_arquivo_grande_demais(monkeypatch):
    monkeypatch.setattr(ing, "TAMANHO_MAXIMO", 1000)
    with pytest.raises(ing.EntradaInvalida, match="limite"):
        ing.ingerir(b"x" * 1001)
