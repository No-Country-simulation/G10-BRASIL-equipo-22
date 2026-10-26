"""Ingestão de documentos clínicos: o nó "Multimodal Ingestion & Text Normalization" do grafo.

Recebe texto, JSON (o contrato de entrada do README), PDF ou imagem e devolve um DocumentoIngerido.
Decide página a página como o documento pode ser lido:

- PDF com camada de texto  -> o texto extraído vai direto para o LLM ("camada_texto")
- PDF escaneado            -> a página vira imagem para o modelo de visão ("pdf_renderizado")
- foto ou scan (JPEG, PNG, WEBP, TIFF) -> imagem endireitada pelo EXIF e reduzida ("imagem_original")

Não chama nenhum modelo. Mede a qualidade de cada imagem e avisa quando ela parece ruim demais
para uma leitura confiável, o que serve de sinal para a revisão humana.

Uso:
    from mediflow_ingestao import ingerir
    doc = ingerir("receita.jpg", canal_origem="Ambulatorio")
    doc.modo_leitura           # "texto", "visao" ou "misto"
    doc.paginas[0].data_url()  # "data:image/jpeg;base64,..." para a API do modelo de visão

    python mediflow_ingestao.py dados_sinteticos/documentos/SINT-018.jpg
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Literal

import numpy as np
import pypdfium2 as pdfium
from PIL import Image, ImageFilter, ImageOps, ImageSequence, UnidentifiedImageError
from pydantic import BaseModel, ConfigDict, Field, ValidationError

TAMANHO_MAXIMO = 20 * 1024 * 1024  # bytes
MAX_PAGINAS = 10
LADO_MAXIMO = 1600  # px; maior lado da imagem enviada ao modelo de visão
QUALIDADE_JPEG = 85
MIN_CARACTERES_PAGINA = 40  # abaixo disso a página do PDF é tratada como escaneada
MIN_LADO_IMAGEM = 600  # px; abaixo disso a foto é pequena demais para ler letra miúda

# Calibrados nos 12 documentos escaneados e fotografados de dados_sinteticos/: o scan ruim (SINT-022)
# tem nitidez 45 e contraste 96; os outros 11 ficam acima de 113 e 147. Com um só exemplo ruim,
# os limites são o ponto médio e geram aviso, não decisão. Recalibrar com documentos reais.
NITIDEZ_MINIMA = 80.0
CONTRASTE_MINIMO = 120.0

TipoArquivo = Literal["TEXTO", "PDF", "IMAGEM"]


class EntradaInvalida(ValueError):
    """Arquivo que não dá para ingerir: vazio, grande demais, corrompido ou em formato não suportado."""


class Pagina(BaseModel):
    numero: int
    origem: Literal["camada_texto", "pdf_renderizado", "imagem_original"]
    texto: str | None = None
    imagem_base64: str | None = None
    mime: str | None = None
    largura: int | None = None
    altura: int | None = None
    nitidez: float | None = None
    contraste: float | None = None

    def data_url(self) -> str:
        if self.imagem_base64 is None:
            raise ValueError(f"a página {self.numero} não tem imagem")
        return f"data:{self.mime};base64,{self.imagem_base64}"


class DocumentoIngerido(BaseModel):
    documento_id: str
    tipo_arquivo: TipoArquivo
    canal_origem: str | None = None
    documento_texto: str | None = None  # campo do contrato do README; None quando só há imagem
    modo_leitura: Literal["texto", "visao", "misto"]
    paginas: list[Pagina]
    nome_arquivo: str | None = None
    sha256: str
    tamanho_bytes: int
    avisos: list[str] = Field(default_factory=list)

    def para_contrato(self) -> dict:
        """A requisição no formato do README (seção 2.3). Documento só em imagem sai com texto None."""
        return {
            "documento_id": self.documento_id,
            "tipo_arquivo": self.tipo_arquivo,
            "documento_texto": self.documento_texto,
            "canal_origem": self.canal_origem,
        }

    def resumo(self) -> dict:
        """Tudo menos as imagens e o texto repetido por página: para log, CLI e depuração."""
        return self.model_dump(exclude={"paginas": {"__all__": {"imagem_base64", "texto"}}})


class _EntradaJson(BaseModel):
    """O contrato de entrada do README."""

    model_config = ConfigDict(str_strip_whitespace=True)

    documento_id: str = Field(min_length=1)
    tipo_arquivo: str | None = None
    documento_texto: str = Field(min_length=1)
    canal_origem: str | None = None


def ingerir(origem: str | Path | bytes, *, nome_arquivo: str | None = None,
            documento_id: str | None = None, canal_origem: str | None = None) -> DocumentoIngerido:
    """Lê um arquivo (caminho ou bytes) e prepara o documento para o motor de extração.

    Num JSON, documento_id e canal_origem do próprio JSON valem; os argumentos só preenchem o que faltar.
    Sem documento_id, gera um a partir do conteúdo: o mesmo arquivo recebe sempre o mesmo id.
    """
    if isinstance(origem, (str, Path)):
        caminho = Path(origem)
        dados = caminho.read_bytes()
        nome_arquivo = nome_arquivo or caminho.name
    else:
        dados = bytes(origem)
    if not dados:
        raise EntradaInvalida("arquivo vazio")
    if len(dados) > TAMANHO_MAXIMO:
        raise EntradaInvalida(f"arquivo de {len(dados) / 2**20:.1f} MB; o limite é {TAMANHO_MAXIMO // 2**20} MB")

    sha256 = hashlib.sha256(dados).hexdigest()
    tipo = detectar_tipo(dados)
    avisos: list[str] = []

    if tipo == "json":
        entrada = _ler_json(dados)
        if documento_id and documento_id != entrada.documento_id:
            avisos.append(f"documento_id do JSON ({entrada.documento_id}) mantido; o informado era {documento_id}")
        documento_id = entrada.documento_id
        canal_origem = entrada.canal_origem or canal_origem
        paginas = [Pagina(numero=1, origem="camada_texto", texto=normalizar(entrada.documento_texto))]
        tipo_arquivo: TipoArquivo = "TEXTO"
    elif tipo == "texto":
        texto = normalizar(dados.decode("utf-8-sig"))
        if not texto:
            raise EntradaInvalida("arquivo de texto sem conteúdo")
        paginas = [Pagina(numero=1, origem="camada_texto", texto=texto)]
        tipo_arquivo = "TEXTO"
    elif tipo == "pdf":
        paginas = _ler_pdf(dados, avisos)
        tipo_arquivo = "PDF"
    else:
        paginas = _ler_imagem(dados, avisos)
        tipo_arquivo = "IMAGEM"

    for pagina in paginas:
        avisos += _avisos_de_qualidade(pagina)

    origens = {p.origem for p in paginas}
    if origens == {"camada_texto"}:
        modo = "texto"
    elif "camada_texto" not in origens:
        modo = "visao"
    else:
        modo = "misto"
    textos = [p.texto for p in paginas if p.texto]

    return DocumentoIngerido(
        documento_id=documento_id or f"DOC-{sha256[:12].upper()}",
        tipo_arquivo=tipo_arquivo,
        canal_origem=canal_origem,
        documento_texto="\n\n".join(textos) or None,
        modo_leitura=modo,
        paginas=paginas,
        nome_arquivo=nome_arquivo,
        sha256=sha256,
        tamanho_bytes=len(dados),
        avisos=avisos,
    )


def detectar_tipo(dados: bytes) -> Literal["pdf", "imagem", "json", "texto"]:
    """Pelo conteúdo, não pela extensão: um .pdf renomeado para .jpg continua sendo PDF."""
    if dados.startswith(b"%PDF-"):
        return "pdf"
    if (dados.startswith(b"\xff\xd8\xff") or dados.startswith(b"\x89PNG\r\n\x1a\n")
            or (dados[:4] == b"RIFF" and dados[8:12] == b"WEBP")
            or dados[:4] in (b"II*\x00", b"MM\x00*")):
        return "imagem"
    try:
        texto = dados.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise EntradaInvalida("formato não suportado: envie PDF, JPEG, PNG, WEBP, TIFF, JSON ou texto UTF-8")
    if any(unicodedata.category(ch) == "Cc" and ch not in "\n\r\t" for ch in texto[:4096]):
        raise EntradaInvalida("arquivo binário em formato não suportado")
    return "json" if texto.lstrip().startswith("{") else "texto"


def normalizar(texto: str) -> str:
    """NFC, quebras de linha Unix, sem caracteres de controle nem espaços repetidos.

    Não junta palavras hifenizadas no fim da linha: em texto clínico o hífen costuma ser
    parte do dado ("CRM-PR", "2026-PS-08790").
    """
    texto = unicodedata.normalize("NFC", texto).replace("\r\n", "\n").replace("\r", "\n")
    texto = "".join(ch for ch in texto if ch in "\n\t" or unicodedata.category(ch)[0] != "C")
    linhas = [re.sub(r"[ \t ]+", " ", linha).strip() for linha in texto.split("\n")]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(linhas)).strip()


def qualidade(imagem: Image.Image) -> tuple[float, float]:
    """(nitidez, contraste) de uma página.

    Nitidez: média do 1% mais forte do laplaciano depois de um filtro de mediana. O filtro tira o
    ruído do scanner, que enganaria a variância do laplaciano pura. Contraste: percentil 99 menos 1.
    """
    cinza = imagem.convert("L")
    cinza.thumbnail((1000, 1000))
    bruto = np.asarray(cinza, dtype=np.float32)
    a = np.asarray(cinza.filter(ImageFilter.MedianFilter(3)), dtype=np.float32)
    lap = np.abs(4 * a[1:-1, 1:-1] - a[:-2, 1:-1] - a[2:, 1:-1] - a[1:-1, :-2] - a[1:-1, 2:])
    topo = np.sort(lap.ravel())[-max(1, lap.size // 100):]
    contraste = np.percentile(bruto, 99) - np.percentile(bruto, 1)
    return round(float(topo.mean()), 1), round(float(contraste), 1)


def _ler_json(dados: bytes) -> _EntradaJson:
    try:
        return _EntradaJson.model_validate_json(dados)
    except ValidationError as erro:
        campos = ", ".join(".".join(map(str, e["loc"])) or "JSON" for e in erro.errors())
        raise EntradaInvalida(f"JSON fora do contrato de entrada (problema em: {campos})") from None


def _ler_pdf(dados: bytes, avisos: list[str]) -> list[Pagina]:
    try:
        pdf = pdfium.PdfDocument(dados)
    except pdfium.PdfiumError as erro:
        raise EntradaInvalida(f"PDF corrompido ou protegido por senha ({erro})") from None
    try:
        total = len(pdf)
        if total == 0:
            raise EntradaInvalida("PDF sem páginas")
        if total > MAX_PAGINAS:
            avisos.append(f"PDF com {total} páginas; só as {MAX_PAGINAS} primeiras foram lidas")
        paginas = []
        for indice in range(min(total, MAX_PAGINAS)):
            pagina = pdf[indice]
            texto = normalizar(pagina.get_textpage().get_text_range())
            if len(re.sub(r"\s", "", texto)) >= MIN_CARACTERES_PAGINA:
                paginas.append(Pagina(numero=indice + 1, origem="camada_texto", texto=texto))
            else:
                largura, altura = pagina.get_size()
                imagem = pagina.render(scale=LADO_MAXIMO / max(largura, altura)).to_pil()
                paginas.append(_pagina_de_imagem(indice + 1, imagem, "pdf_renderizado"))
        return paginas
    finally:
        pdf.close()


def _ler_imagem(dados: bytes, avisos: list[str]) -> list[Pagina]:
    try:
        imagem = Image.open(io.BytesIO(dados))
        quadros = []
        for i, quadro in enumerate(ImageSequence.Iterator(imagem)):
            if i == MAX_PAGINAS:
                avisos.append(f"imagem com mais de {MAX_PAGINAS} páginas; só as {MAX_PAGINAS} primeiras foram lidas")
                break
            quadros.append(ImageOps.exif_transpose(quadro.copy()))  # foto de celular "deitada"
    except Image.DecompressionBombError:
        raise EntradaInvalida("imagem com resolução absurda (possível arquivo malicioso)") from None
    except (UnidentifiedImageError, OSError) as erro:
        raise EntradaInvalida(f"imagem corrompida ou em formato não suportado ({erro})") from None
    paginas = []
    for numero, quadro in enumerate(quadros, start=1):
        if min(quadro.size) < MIN_LADO_IMAGEM:
            avisos.append(f"página {numero}: resolução baixa ({quadro.width}x{quadro.height} px)")
        paginas.append(_pagina_de_imagem(numero, quadro, "imagem_original"))
    return paginas


def _pagina_de_imagem(numero: int, imagem: Image.Image, origem: str) -> Pagina:
    imagem = imagem.convert("RGB")
    if max(imagem.size) > LADO_MAXIMO:
        imagem.thumbnail((LADO_MAXIMO, LADO_MAXIMO), Image.Resampling.LANCZOS)
    nitidez, contraste = qualidade(imagem)
    saida = io.BytesIO()
    imagem.save(saida, "JPEG", quality=QUALIDADE_JPEG)
    return Pagina(numero=numero, origem=origem, imagem_base64=base64.b64encode(saida.getvalue()).decode("ascii"),
                  mime="image/jpeg", largura=imagem.width, altura=imagem.height,
                  nitidez=nitidez, contraste=contraste)


def _avisos_de_qualidade(pagina: Pagina) -> list[str]:
    avisos = []
    if pagina.nitidez is not None and pagina.nitidez < NITIDEZ_MINIMA:
        avisos.append(f"página {pagina.numero}: imagem borrada (nitidez {pagina.nitidez}); considerar revisão humana")
    if pagina.contraste is not None and pagina.contraste < CONTRASTE_MINIMO:
        avisos.append(f"página {pagina.numero}: contraste baixo ({pagina.contraste}); considerar revisão humana")
    return avisos


def main():
    parser = argparse.ArgumentParser(description="Ingere um documento clínico e mostra o resultado, sem as imagens.")
    parser.add_argument("arquivo")
    parser.add_argument("--canal", help="canal de origem, ex.: Pronto_Socorro")
    parser.add_argument("--id", help="documento_id; sem ele, é gerado a partir do conteúdo")
    args = parser.parse_args()
    try:
        doc = ingerir(args.arquivo, documento_id=args.id, canal_origem=args.canal)
    except (EntradaInvalida, OSError) as erro:
        sys.exit(f"erro: {erro}")
    print(json.dumps(doc.resumo(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
