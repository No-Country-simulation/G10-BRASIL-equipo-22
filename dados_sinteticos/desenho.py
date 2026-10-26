"""Desenha os documentos em PDF e simula digitalização e foto de celular."""
import math
from datetime import datetime
from pathlib import Path

import numpy as np
import pypdfium2 as pdfium
from PIL import Image, ImageFilter
from reportlab.lib.pagesizes import A4, A5
from reportlab.lib.utils import simpleSplit
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from modelo import AVISO, TOKEN, Doc, Guia

FONTES = Path(__file__).parent / "fontes"
pdfmetrics.registerFont(TTFont("MaoLegivel", str(FONTES / "Kalam-Regular.ttf")))
pdfmetrics.registerFont(TTFont("MaoRuim", str(FONTES / "HomemadeApple-Regular.ttf")))
LETRAS = {"legivel": ("MaoLegivel", 14), "ruim": ("MaoRuim", 12)}

PRETO = (0, 0, 0)
CINZA = (0.35, 0.35, 0.35)
TINTA = (0.10, 0.16, 0.45)  # caneta esferográfica azul
PRETO_CANETA = (0.03, 0.03, 0.06)
TINTA_CARIMBO = (0.36, 0.20, 0.55)
MARGEM = 36
# Metadados fixos: o mesmo caso gera sempre o mesmo arquivo (sem isso o Pillow grava a hora atual).
DATA_FIXA = datetime(2026, 10, 26).timetuple()


class Folha:
    """Uma página com cursor vertical, do topo para baixo."""

    def __init__(self, c, tamanho, rng):
        self.c = c
        self.largura, self.altura = tamanho
        self.rng = rng
        self.x0, self.x1 = MARGEM, self.largura - MARGEM
        self.y = self.altura - MARGEM

    @property
    def util(self):
        return self.x1 - self.x0

    def escrever(self, texto, fonte="Helvetica", tam=10, x=None, cor=PRETO, entrelinha=1.3):
        self.y -= tam * entrelinha
        self.c.setFillColorRGB(*cor)
        self.c.setFont(fonte, tam)
        self.c.drawString(self.x0 if x is None else x, self.y, texto)

    def paragrafo(self, texto, fonte="Helvetica", tam=10, recuo=0, cor=PRETO, entrelinha=1.35):
        for linha in simpleSplit(texto, fonte, tam, self.util - recuo):
            self.escrever(linha, fonte, tam, self.x0 + recuo, cor, entrelinha)

    def traco(self, cor=CINZA, espessura=0.6):
        self.c.setStrokeColorRGB(*cor)
        self.c.setLineWidth(espessura)
        self.c.line(self.x0, self.y, self.x1, self.y)

    # --- escrita à mão --------------------------------------------------------------------
    def mao(self, texto, x, y, letra="legivel"):
        """Escreve à mão a partir de (x, y), com tremor na linha de base e na inclinação."""
        fonte, tam = LETRAS[letra]
        c, rng = self.c, self.rng
        c.saveState()
        c.translate(x + rng.uniform(-2, 2), y + rng.uniform(-1.5, 1.5))
        c.rotate(rng.uniform(-1.5, 1.5))
        c.setFillColorRGB(*TINTA)
        cx, pos = 0.0, 0
        for m in TOKEN.finditer(texto):
            cx = self._trecho(texto[pos:m.start()], cx, fonte, tam)
            if m.group(1) == "ILEGIVEL":
                largura = int(m.group(2)) * tam * 0.45
                self.rabisco(cx, -2, largura, tam * 0.9)
                cx += largura
            else:
                # A caneta azul escreveu "antes"; depois alguém reescreveu "depois" por cima,
                # com caneta preta e mais força, e riscou o original. Os dois ficam visíveis.
                antes, depois = m.group(2).split(">")
                x_antes = cx + stringWidth(depois[:-len(antes)], fonte, tam * 1.15) + 3
                c.setFont(fonte, tam)
                c.drawString(x_antes, 2, antes)
                c.setFillColorRGB(*PRETO_CANETA)
                c.setFont(fonte, tam * 1.15)
                c.drawString(cx, -1.5, depois)
                self.rabisco(x_antes - 1, tam * 0.2, stringWidth(antes, fonte, tam) + 3, tam * 0.55,
                             espessura=0.7, cor=PRETO_CANETA)
                c.setFillColorRGB(*TINTA)
                cx += stringWidth(depois, fonte, tam * 1.15) + 4
            pos = m.end()
        self._trecho(texto[pos:], cx, fonte, tam)
        c.restoreState()

    def _trecho(self, trecho, cx, fonte, tam):
        espaco = stringWidth(" ", fonte, tam)
        for i, palavra in enumerate(trecho.split(" ")):
            if i:
                cx += espaco
            if palavra:
                self.c.setFont(fonte, tam)
                self.c.drawString(cx, self.rng.uniform(-0.8, 0.8), palavra)
                cx += stringWidth(palavra, fonte, tam)
        return cx

    def rabisco(self, x, y, largura, altura, espessura=0.9, cor=TINTA):
        """Palavra ilegível: laçadas que parecem letra cursiva sem formar letra nenhuma."""
        c, rng = self.c, self.rng
        p = c.beginPath()
        p.moveTo(x, y + altura * rng.uniform(0.2, 0.6))
        cx = x
        while cx < x + largura:
            passo = rng.uniform(3, 7)
            p.curveTo(cx + passo * 0.2, y + altura * rng.uniform(0.7, 1.3),
                      cx + passo * 0.8, y + altura * rng.uniform(-0.3, 0.3),
                      cx + passo, y + altura * rng.uniform(0.1, 0.6))
            cx += passo
        c.setStrokeColorRGB(*cor)
        c.setLineWidth(espessura)
        c.drawPath(p, stroke=1, fill=0)

    def rubrica(self, x, y, largura=110):
        c, rng = self.c, self.rng
        p = c.beginPath()
        p.moveTo(x, y)
        cx = x
        while cx < x + largura:
            passo = rng.uniform(8, 18)
            p.curveTo(cx + passo * 0.1, y + rng.uniform(8, 22),
                      cx + passo * 0.9, y + rng.uniform(-10, 4),
                      cx + passo, y + rng.uniform(-3, 6))
            cx += passo
        p.lineTo(cx + 18, y + rng.uniform(-2, 4))
        c.setStrokeColorRGB(*TINTA)
        c.setLineWidth(1.1)
        c.drawPath(p, stroke=1, fill=0)

    def carimbo(self, linhas, x, y, borrao=False):
        c, rng = self.c, self.rng
        tam = 8.5
        w = max(stringWidth(t, "Helvetica-Bold", tam) for t in linhas) + 16
        h = len(linhas) * (tam + 3) + 8
        c.saveState()
        c.translate(x, y)
        c.rotate(rng.uniform(-7, -3))
        c.setStrokeColorRGB(*TINTA_CARIMBO)
        c.setFillColorRGB(*TINTA_CARIMBO)
        c.setStrokeAlpha(0.8)
        c.setFillAlpha(0.8)
        c.setLineWidth(1.2)
        c.roundRect(0, 0, w, h, 4, stroke=1, fill=0)
        c.setFont("Helvetica-Bold", tam)
        for i, texto in enumerate(linhas):
            c.drawCentredString(w / 2, h - (i + 1) * (tam + 3) - 1, texto)
        if borrao:
            ultima = h - len(linhas) * (tam + 3) - 1
            self.borrao(w / 2, ultima + tam * 0.35, w * 0.36, tam * 0.7)
        c.restoreState()

    def borrao(self, cx, cy, rx, ry):
        """Mancha de tinta que cobre o que está embaixo."""
        c, rng = self.c, self.rng
        c.setFillColorRGB(0.08, 0.09, 0.28)
        c.setFillAlpha(1)
        p = c.beginPath()
        n = 22
        for i in range(n):
            ang = 2 * math.pi * i / n
            r = rng.uniform(0.85, 1.15)
            px, py = cx + rx * r * math.cos(ang), cy + ry * r * math.sin(ang)
            if i == 0:
                p.moveTo(px, py)
            else:
                p.lineTo(px, py)
        p.close()
        c.drawPath(p, stroke=0, fill=1)
        for _ in range(5):
            ang = rng.uniform(0, 2 * math.pi)
            dist = rng.uniform(1.15, 1.6)
            c.circle(cx + rx * dist * math.cos(ang), cy + ry * dist * math.sin(ang),
                     rng.uniform(0.8, 2.2), stroke=0, fill=1)


# --- Documento em texto corrido ---------------------------------------------------------------

def desenhar_doc(c, d: Doc, rng):
    f = Folha(c, A5 if d.tamanho == "A5" else A4, rng)
    centro = f.largura / 2
    a_mao = d.manuscrito or any(b[0] == "mao" for b in d.blocos)

    f.paragrafo(d.instituicao, "Helvetica-Bold", 12.5 if d.tamanho == "A4" else 11.5, entrelinha=1.2)
    f.paragrafo(d.endereco, "Helvetica", 7.5, cor=CINZA, entrelinha=1.4)
    f.y -= 6
    f.traco()
    if d.titulo:
        f.y -= 20
        c.setFillColorRGB(*PRETO)
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(centro, f.y, d.titulo)
        f.y -= 4

    _campos(f, d)
    if d.campos:
        f.y -= 8
        f.traco(cor=(0.75, 0.75, 0.75), espessura=0.4)

    n_med = 0
    for bloco in d.blocos:
        tipo = bloco[0]
        if tipo == "secao":
            f.y -= 6
            f.escrever(bloco[1].upper(), "Helvetica-Bold", 9.5)
        elif tipo == "par":
            f.y -= 2
            f.paragrafo(bloco[1])
        elif tipo == "destaque":
            _destaque(f, bloco[1])
        elif tipo == "med":
            n_med += 1
            _medicamento(f, n_med, *bloco[1:])
        elif tipo == "tabela":
            _tabela(f, bloco[1], bloco[2])
        elif tipo == "linha":
            f.y -= 24 if d.manuscrito else 14
            if d.manuscrito:
                f.mao(bloco[1], f.x0, f.y, d.letra)
            else:
                c.setFont("Helvetica", 10)
                c.drawString(f.x0, f.y, bloco[1])
        elif tipo == "impresso":
            f.escrever(bloco[1], "Helvetica", 10.5, entrelinha=2.0)
        elif tipo == "mao":
            f.y -= 26
            c.setStrokeColorRGB(*CINZA)
            c.setLineWidth(0.5)
            c.line(f.x0, f.y - 4, f.x0 + bloco[2], f.y - 4)
            f.mao(bloco[1], f.x0 + 8, f.y, "legivel")

    # assinatura, sempre no terço de baixo
    piso = MARGEM + (70 if d.carimbo else 45)
    y_ass = max(piso, min(f.y - 70, 0.28 * f.altura))
    if d.local_data:
        if a_mao:
            f.mao(d.local_data, f.x0, y_ass + 42, d.letra if d.manuscrito else "legivel")
        else:
            c.setFillColorRGB(*PRETO)
            c.setFont("Helvetica", 9.5)
            c.drawString(f.x0, y_ass + 42, d.local_data)
    f.rubrica(centro - 55, y_ass + 8)
    c.setStrokeColorRGB(*PRETO)
    c.setLineWidth(0.5)
    c.line(centro - 95, y_ass, centro + 95, y_ass)
    c.setFillColorRGB(*PRETO)
    for i, texto in enumerate(d.assinatura):
        c.setFont("Helvetica-Bold" if i == 0 else "Helvetica", 9 if i == 0 else 8)
        c.drawCentredString(centro, y_ass - 12 - 11 * i, texto)
    if d.carimbo:
        f.carimbo(d.carimbo, centro - 60, y_ass - 58, d.borrao_no_carimbo)
    _rodape(c, f.largura)


def _campos(f, d: Doc):
    """Campos de identificação; no A4 cabem dois por linha quando são curtos."""
    c = f.c
    colunas = 2 if d.tamanho == "A4" else 1
    largura_col = f.util / colunas
    col = colunas  # força nova linha no primeiro campo
    for rotulo, valor in d.campos:
        rot = f"{rotulo}:"
        x_rot = stringWidth(rot, "Helvetica-Bold", 9) + 5
        largo = x_rot + stringWidth(valor or "x" * 30, "Helvetica", 10) > largura_col - 8
        if col >= colunas or largo:
            f.y -= 22 if d.manuscrito else 15
            col = 0
        x = f.x0 + col * largura_col
        c.setFillColorRGB(*PRETO)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(x, f.y, rot)
        if not valor:
            c.setStrokeColorRGB(*CINZA)
            c.setLineWidth(0.5)
            c.line(x + x_rot, f.y - 2, x + x_rot + 170, f.y - 2)
        elif d.manuscrito:
            f.mao(valor, x + x_rot, f.y, d.letra)
        else:
            c.setFont("Helvetica", 10)
            c.drawString(x + x_rot, f.y, valor)
        col = colunas if largo else col + 1


def _medicamento(f, n, nome, qtde, uso):
    c = f.c
    f.y -= 18
    c.setFillColorRGB(*PRETO)
    c.setFont("Helvetica-Bold", 10)
    rotulo = f"{n}. {nome}"
    c.drawString(f.x0, f.y, rotulo)
    c.setFont("Helvetica", 10)
    c.drawRightString(f.x1, f.y, qtde)
    inicio = f.x0 + stringWidth(rotulo, "Helvetica-Bold", 10) + 6
    fim = f.x1 - stringWidth(qtde, "Helvetica", 10) - 6
    c.setFillColorRGB(*CINZA)
    pontos = "." * max(0, int((fim - inicio) / stringWidth(".", "Helvetica", 10)))
    c.drawString(inicio, f.y, pontos)
    f.paragrafo(uso, recuo=16, entrelinha=1.4)


def _destaque(f, texto):
    c = f.c
    linhas = simpleSplit(texto, "Helvetica-Bold", 9.5, f.util - 16)
    altura = len(linhas) * 13 + 10
    f.y -= altura + 8
    c.setFillColorRGB(0.95, 0.95, 0.95)
    c.setStrokeColorRGB(*PRETO)
    c.setLineWidth(1)
    c.rect(f.x0, f.y, f.util, altura, stroke=1, fill=1)
    c.setFillColorRGB(*PRETO)
    c.setFont("Helvetica-Bold", 9.5)
    for i, linha in enumerate(linhas):
        c.drawString(f.x0 + 8, f.y + altura - 15 - 13 * i, linha)


def _tabela(f, cabecalho, linhas):
    c = f.c
    proporcoes = [0.38, 0.15, 0.17, 0.30]
    xs = [f.x0]
    for p in proporcoes[:-1]:
        xs.append(xs[-1] + p * f.util)
    passo = 15
    f.y -= passo + 4
    c.setFillColorRGB(0.90, 0.90, 0.90)
    c.rect(f.x0, f.y - 4, f.util, passo, stroke=0, fill=1)
    c.setFillColorRGB(*PRETO)
    c.setFont("Helvetica-Bold", 8.5)
    for x, texto in zip(xs, cabecalho):
        c.drawString(x + 3, f.y, texto)
    for linha in linhas:
        f.y -= passo
        for i, (x, texto) in enumerate(zip(xs, linha)):
            c.setFont("Helvetica-Bold" if i == 1 else "Helvetica", 9)
            c.drawString(x + 3, f.y, texto)
        c.setStrokeColorRGB(0.82, 0.82, 0.82)
        c.setLineWidth(0.4)
        c.line(f.x0, f.y - 4, f.x1, f.y - 4)
    f.y -= 6


def _rodape(c, largura):
    c.setFillColorRGB(0.45, 0.45, 0.45)
    c.setFont("Helvetica-Oblique", 6.5)
    c.drawCentredString(largura / 2, 16, AVISO)


# --- Guia SP/SADT -------------------------------------------------------------------------------

def desenhar_guia(c, g: Guia, rng):
    f = Folha(c, A4, rng)
    titulo = ("GUIA DE SERVIÇO PROFISSIONAL / SERVIÇO AUXILIAR DE DIAGNÓSTICO E TERAPIA - SP/SADT")
    _linha_caixas(f, 46, [(0.26, "", g.operadora, True), (0.50, "", titulo, True),
                          (0.24, "2 - Nº Guia no Prestador", g.numero_guia, False)])
    _linha_caixas(f, 28, [(0.20, "1 - Registro ANS", g.registro_ans), (0.20, "3 - Nº Guia Principal", ""),
                          (0.20, "4 - Data da Autorização", ""), (0.18, "5 - Senha", ""),
                          (0.22, "6 - Data de Validade da Senha", "")])
    _faixa(f, "DADOS DO BENEFICIÁRIO")
    _linha_caixas(f, 28, [(0.30, "8 - Número da Carteira", g.carteira),
                          (0.16, "9 - Validade da Carteira", ""), (0.54, "10 - Nome", g.beneficiario)])
    _faixa(f, "DADOS DO SOLICITANTE")
    _linha_caixas(f, 28, [(0.25, "13 - Código na Operadora", ""),
                          (0.75, "14 - Nome do Contratado", g.contratado)])
    _linha_caixas(f, 28, [(0.38, "15 - Nome do Profissional Solicitante", g.profissional),
                          (0.15, "16 - Conselho Profissional", g.conselho),
                          (0.20, "17 - Número no Conselho", g.numero_conselho),
                          (0.09, "18 - UF", g.uf), (0.18, "19 - Código CBO", g.cbo)])
    _faixa(f, "DADOS DA SOLICITAÇÃO / PROCEDIMENTOS OU EXAMES SOLICITADOS")
    _linha_caixas(f, 28, [(0.5, "21 - Caráter do Atendimento", g.carater),
                          (0.5, "22 - Data da Solicitação", g.data_solicitacao)])
    _linha_caixas(f, 50, [(1.0, "23 - Indicação Clínica", g.indicacao_clinica)])
    colunas = [(0.10, "24 - Tabela"), (0.18, "25 - Código do Procedimento"), (0.52, "26 - Descrição"),
               (0.10, "27 - Qtde. Solic."), (0.10, "28 - Qtde. Aut.")]
    procedimentos = list(g.procedimentos) + [("", "", "", "")] * (4 - len(g.procedimentos))
    for i, proc in enumerate(procedimentos):
        rotulos = [r for _, r in colunas] if i == 0 else [""] * len(colunas)
        _linha_caixas(f, 26 if i == 0 else 18,
                      [(p, r, v) for (p, _), r, v in zip(colunas, rotulos, list(proc) + [""])])
    f.y -= 10
    y_caixa = f.y
    _linha_caixas(f, 60, [(0.5, "Data e Assinatura do Profissional Solicitante", g.data_solicitacao),
                          (0.5, "Data e Assinatura do Beneficiário ou Responsável", "")])
    f.rubrica(f.x0 + 60, y_caixa - 45, 90)
    _rodape(c, f.largura)


def _faixa(f, texto):
    c = f.c
    f.y -= 16
    c.setFillColorRGB(0.85, 0.85, 0.85)
    c.rect(f.x0, f.y, f.util, 13, stroke=0, fill=1)
    c.setFillColorRGB(*PRETO)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(f.x0 + 4, f.y + 3.5, texto)
    f.y -= 2


def _linha_caixas(f, altura, itens):
    c = f.c
    f.y -= altura
    x = f.x0
    for item in itens:
        proporcao, rotulo, valor = item[:3]
        destaque = item[3] if len(item) > 3 else False
        w = proporcao * f.util
        c.setStrokeColorRGB(*PRETO)
        c.setLineWidth(0.6)
        c.rect(x, f.y, w, altura, stroke=1, fill=0)
        c.setFillColorRGB(0.25, 0.25, 0.25)
        c.setFont("Helvetica", 5.8)
        if rotulo:
            c.drawString(x + 3, f.y + altura - 8, rotulo)
        c.setFillColorRGB(*PRETO)
        fonte, tam = ("Helvetica-Bold", 9) if destaque else ("Helvetica", 9)
        topo = f.y + altura - (19 if rotulo else 14)
        for i, linha in enumerate(simpleSplit(valor, fonte, tam, w - 8)):
            c.setFont(fonte, tam)
            c.drawString(x + 4, topo - 11 * i, linha)
        x += w
    f.y -= 2


# --- Arquivos -----------------------------------------------------------------------------------

def gerar_pdf(documento: Doc | Guia, caminho: Path, rng, titulo: str):
    tamanho = A5 if isinstance(documento, Doc) and documento.tamanho == "A5" else A4
    c = canvas.Canvas(str(caminho), pagesize=tamanho, invariant=1)
    c.setTitle(titulo)
    c.setAuthor("MediFlow - dados sintéticos")
    c.setSubject(AVISO)
    if isinstance(documento, Guia):
        desenhar_guia(c, documento, rng)
    else:
        desenhar_doc(c, documento, rng)
    c.showPage()
    c.save()


def rasterizar(caminho_pdf: Path, dpi: int) -> Image.Image:
    pdf = pdfium.PdfDocument(str(caminho_pdf))
    imagem = pdf[0].render(scale=dpi / 72).to_pil().convert("RGB")
    pdf.close()
    return imagem


def texto_do_pdf(caminho_pdf: Path) -> str:
    pdf = pdfium.PdfDocument(str(caminho_pdf))
    texto = pdf[0].get_textpage().get_text_range()
    pdf.close()
    return texto


PAPEL = np.array([247, 244, 235], dtype=np.float32)


def digitalizar(imagem: Image.Image, rng: np.random.Generator, pesado: bool) -> Image.Image:
    """Scanner de mesa: papel amarelado, página torta, borrão, ruído; no pesado, xerox de xerox."""
    arr = np.asarray(imagem, dtype=np.float32) * (PAPEL / 255)
    imagem = Image.fromarray(arr.clip(0, 255).astype(np.uint8))
    angulo = rng.uniform(-2.2, 2.2) if pesado else rng.uniform(-0.9, 0.9)
    imagem = imagem.rotate(angulo, resample=Image.BICUBIC, fillcolor=tuple(int(v) for v in PAPEL))
    if pesado:
        largura, altura = imagem.size
        imagem = imagem.resize((int(largura * 0.5), int(altura * 0.5)), Image.BILINEAR)
        imagem = imagem.resize((largura, altura), Image.BILINEAR)
    imagem = imagem.filter(ImageFilter.GaussianBlur(1.0 if pesado else 0.45))
    arr = np.asarray(imagem, dtype=np.float32)
    arr += rng.normal(0, 13 if pesado else 4, arr.shape[:2])[..., None]
    if pesado:
        arr = 135 + (arr - 128) * 0.72  # contraste lavado
        manchas = rng.random(arr.shape[:2]) < 0.0015
        arr[manchas] = rng.uniform(20, 90)
    # sombra da tampa do scanner na borda esquerda
    largura = arr.shape[1]
    sombra = np.clip(np.linspace(0.55, 1.0, max(1, largura // 30)), 0, 1)
    arr[:, : len(sombra)] *= sombra[None, :, None]
    return Image.fromarray(arr.clip(0, 255).astype(np.uint8))


def fotografar(imagem: Image.Image, rng: np.random.Generator) -> Image.Image:
    """Foto de celular: página sobre a mesa, em perspectiva, com luz desigual."""
    largura, altura = imagem.size
    fw, fh = int(largura * 1.22), int(altura * 1.16)
    mx, my = (fw - largura) / 2, (fh - altura) / 2

    # mesa de madeira: veios verticais que derivam devagar, mais manchas suaves
    folga = 40
    colunas = np.convolve(rng.normal(0, 1, fw + 2 * folga), np.ones(7) / 7, mode="same")
    deriva = folga + (folga * 0.6 * np.sin(2 * np.pi * np.arange(fh) / fh * rng.uniform(0.6, 1.4))).astype(int)
    veios = colunas[np.arange(fw)[None, :] + deriva[:, None]] * 26
    manchas = Image.fromarray(rng.normal(0, 1, (6, 8)).astype(np.float32), mode="F")
    manchas = np.asarray(manchas.resize((fw, fh), Image.BICUBIC)) * 9
    mesa = np.empty((fh, fw, 3), dtype=np.float32)
    mesa[...] = np.array([122, 88, 58], dtype=np.float32)
    mesa += (veios + manchas + rng.normal(0, 4, (fh, fw)))[..., None]

    def j(v):
        return rng.uniform(-v, v)

    cantos_saida = [(mx + j(40), my + j(30)), (mx + largura + j(40), my + j(30)),
                    (mx + largura + j(25), my + altura + j(25)), (mx + j(25), my + altura + j(25))]
    cantos_pagina = [(0, 0), (largura, 0), (largura, altura), (0, altura)]
    coef = _coeficientes(cantos_saida, cantos_pagina)
    pagina = imagem.transform((fw, fh), Image.PERSPECTIVE, coef, Image.BICUBIC)
    mascara = Image.new("L", imagem.size, 255).transform((fw, fh), Image.PERSPECTIVE, coef, Image.BICUBIC)
    fundo = Image.fromarray(mesa.clip(0, 255).astype(np.uint8))
    foto = Image.composite(pagina, fundo, mascara)

    # luz: um canto mais claro, o oposto na sombra; tom quente de lâmpada
    arr = np.asarray(foto, dtype=np.float32)
    yy, xx = np.mgrid[0:fh, 0:fw]
    ox, oy = rng.uniform(0, fw), rng.uniform(0, fh * 0.4)
    dist = np.sqrt((xx - ox) ** 2 + (yy - oy) ** 2) / math.hypot(fw, fh)
    arr *= (1.08 - 0.38 * dist)[..., None]
    arr *= np.array([1.03, 1.0, 0.92], dtype=np.float32)
    arr += rng.normal(0, 5, arr.shape[:2])[..., None]
    foto = Image.fromarray(arr.clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.7))
    escala = 1600 / max(foto.size)
    if escala < 1:
        foto = foto.resize((int(foto.width * escala), int(foto.height * escala)), Image.LANCZOS)
    return foto


def _coeficientes(saida, entrada):
    """Coeficientes da transformação de perspectiva do Pillow (ponto de saída -> ponto de entrada)."""
    a, b = [], []
    for (x, y), (u, v) in zip(saida, entrada):
        a.append([x, y, 1, 0, 0, 0, -u * x, -u * y])
        b.append(u)
        a.append([0, 0, 0, x, y, 1, -v * x, -v * y])
        b.append(v)
    return np.linalg.solve(np.array(a, dtype=float), np.array(b, dtype=float)).tolist()


def salvar_jpg(imagem: Image.Image, caminho: Path, qualidade: int):
    imagem.save(caminho, "JPEG", quality=qualidade, optimize=True)


def salvar_pdf_imagem(imagem: Image.Image, caminho: Path, dpi: int, titulo: str):
    """PDF só com a imagem, como sai de um scanner: sem camada de texto."""
    imagem.save(caminho, "PDF", resolution=dpi, title=titulo, author="MediFlow - dados sintéticos",
                subject=AVISO, creationDate=DATA_FIXA, modDate=DATA_FIXA, quality=70)
