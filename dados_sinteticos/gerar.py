"""Gera os documentos sintéticos, o gabarito e o manifesto.

Uso:  .venv/bin/python gerar.py

Antes de escrever qualquer arquivo, confere se o gabarito de cada caso bate com o próprio
documento (nome, CRM, medicamentos, doses, idade) e se as regras de roteamento são coerentes.
O mesmo caso gera sempre o mesmo arquivo (sementes fixas e metadados sem data atual).
"""
import csv
import json
import random
import re
import sys
import tempfile
from collections import Counter
from pathlib import Path

import numpy as np

from casos import CASOS
from desenho import (digitalizar, fotografar, gerar_pdf, rasterizar, salvar_jpg, salvar_pdf_imagem,
                     texto_do_pdf)
from modelo import (CENARIOS, DEGRADACOES, DESTINOS, EMERGENCIA, FORMATOS, REVISAO, Caso,
                    transcrever)

RAIZ = Path(__file__).parent
DOCUMENTOS = RAIZ / "documentos"
GABARITO = RAIZ / "gabarito"
DPI = 150
TIPO_ARQUIVO = {"texto": "TEXTO", "pdf_digital": "PDF", "pdf_escaneado": "PDF", "imagem": "IMAGEM"}


def sem_espacos(texto: str) -> str:
    """Para comparar valores: ignora espaços e maiúsculas, mas não acentos."""
    return re.sub(r"\s+", "", texto).casefold()


def conferir(caso: Caso) -> list[str]:
    erros = []
    esperado = caso.esperado
    dados = esperado["dados_extraidos"]
    rota = esperado["decisao_roteamento"]
    prioridade = esperado["classificacao"]["nivel_prioridade"]
    texto = transcrever(caso.documento)
    compacto = sem_espacos(texto)

    def presente(valor, campo):
        if valor is not None and sem_espacos(str(valor)) not in compacto:
            erros.append(f"{campo} {valor!r} não aparece no documento")

    presente(dados["paciente"]["nome"], "paciente.nome")
    if dados["paciente"]["idade"] is not None:
        presente(f"{dados['paciente']['idade']} anos", "paciente.idade")
    presente(dados["medico_solicitante"]["nome"], "medico_solicitante.nome")
    if dados["medico_solicitante"]["crm"]:
        presente(dados["medico_solicitante"]["crm"].split("-")[0], "medico_solicitante.crm")
    for i, med in enumerate(dados["medicamentos"]):
        presente(med["nome"], f"medicamentos[{i}].nome")
        presente(med["dosagem"], f"medicamentos[{i}].dosagem")
        if med["nome"] is None and not any("medicamentos" in c for c in caso.campos_ausentes):
            erros.append(f"medicamentos[{i}] sem nome e sem registro em campos_ausentes")
    for exame in dados["exames_solicitados"]:
        presente(exame, "exames_solicitados")

    cid = dados["cid_sugerido"]
    if caso.cid_aceitos and cid not in caso.cid_aceitos:
        erros.append(f"cid_sugerido {cid!r} fora de cid_aceitos")
    if caso.cenario not in CENARIOS:
        erros.append(f"cenário desconhecido: {caso.cenario}")
    if caso.formato not in FORMATOS or caso.degradacao not in DEGRADACOES:
        erros.append("formato ou degradação desconhecidos")
    if (caso.formato in ("texto", "pdf_digital")) != (caso.degradacao == "nenhuma"):
        erros.append("texto e PDF digital não têm degradação; escaneado e imagem têm")

    destino = rota["destino_principal"]
    if destino not in DESTINOS:
        erros.append(f"destino desconhecido: {destino}")
    if prioridade == "Urgente" and destino != EMERGENCIA and not caso.decisao_pendente:
        erros.append("urgente fora da fila de emergência sem decisão pendente registrada")
    if (destino == EMERGENCIA) != (rota["notificacao_gerada"] is not None):
        erros.append("fila de emergência e alerta ao plantão andam juntos")
    revisao_esperada = destino == REVISAO or (destino == EMERGENCIA and bool(caso.campos_ausentes))
    if rota["requer_auditoria_humana"] != revisao_esperada:
        erros.append("requer_auditoria_humana incoerente com o destino e os campos ausentes")
    if (destino == REVISAO) != (caso.cenario == "ambiguo"):
        erros.append("todo caso ambíguo vai para revisão humana, e só eles")
    return erros


def gerar_documento(caso: Caso, rascunhos: Path) -> Path:
    semente = int(caso.id.split("-")[1])
    rng_pdf = random.Random(semente)
    rng_img = np.random.default_rng(semente)

    if caso.formato == "texto":
        caminho = DOCUMENTOS / f"{caso.id}.json"
        entrada = {
            "documento_id": caso.id,
            "tipo_arquivo": "TEXTO",
            "documento_texto": transcrever(caso.documento),
            "canal_origem": caso.canal_origem,
        }
        caminho.write_text(json.dumps(entrada, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return caminho

    if caso.formato == "pdf_digital":
        caminho = DOCUMENTOS / f"{caso.id}.pdf"
        gerar_pdf(caso.documento, caminho, rng_pdf, caso.id)
        return caminho

    # Escaneado ou imagem: desenha um PDF de rascunho e "passa no scanner" ou "fotografa".
    rascunho = rascunhos / f"{caso.id}.pdf"
    gerar_pdf(caso.documento, rascunho, rng_pdf, caso.id)
    if caso.degradacao == "foto":
        imagem = fotografar(rasterizar(rascunho, 170), rng_img)
    else:
        imagem = digitalizar(rasterizar(rascunho, DPI), rng_img, pesado=caso.degradacao == "scan_pesado")
    if caso.formato == "imagem":
        caminho = DOCUMENTOS / f"{caso.id}.jpg"
        salvar_jpg(imagem, caminho, 45 if caso.degradacao == "scan_pesado" else 82)
    else:
        caminho = DOCUMENTOS / f"{caso.id}.pdf"
        salvar_pdf_imagem(imagem, caminho, DPI, caso.id)
    return caminho


def gabarito_completo(caso: Caso, arquivo: Path) -> dict:
    return {
        "documento_id": caso.id,
        **caso.esperado,
        "_avaliacao": {
            "cenario": caso.cenario,
            "formato": caso.formato,
            "degradacao": caso.degradacao,
            "arquivo": arquivo.relative_to(RAIZ).as_posix(),
            "tipo_arquivo": TIPO_ARQUIVO[caso.formato],
            "canal_origem": caso.canal_origem,
            "motivo": caso.motivo,
            "armadilha": caso.armadilha,
            "cid_aceitos": caso.cid_aceitos,
            "campos_ausentes": caso.campos_ausentes,
            "decisao_pendente": caso.decisao_pendente,
            "transcricao": transcrever(caso.documento),
        },
    }


def main():
    repetidos = [i for i, n in Counter(c.id for c in CASOS).items() if n > 1]
    problemas = {c.id: conferir(c) for c in CASOS}
    problemas = {i: e for i, e in problemas.items() if e}
    if repetidos or problemas:
        for i in repetidos:
            print(f"{i}: id repetido")
        for i, erros in problemas.items():
            for erro in erros:
                print(f"{i}: {erro}")
        sys.exit(1)

    DOCUMENTOS.mkdir(exist_ok=True)
    GABARITO.mkdir(exist_ok=True)
    for antigo in [*DOCUMENTOS.glob("SINT-*"), *GABARITO.glob("SINT-*")]:
        antigo.unlink()

    manifesto = []
    with tempfile.TemporaryDirectory() as tmp:
        for caso in CASOS:
            arquivo = gerar_documento(caso, Path(tmp))
            if caso.formato == "pdf_digital":
                dados = caso.esperado["dados_extraidos"]
                procurado = dados["paciente"]["nome"] or dados["medico_solicitante"]["nome"]
                if sem_espacos(procurado) not in sem_espacos(texto_do_pdf(arquivo)):
                    sys.exit(f"{caso.id}: o PDF digital não tem camada de texto legível")
            gab = gabarito_completo(caso, arquivo)
            (GABARITO / f"{caso.id}.json").write_text(
                json.dumps(gab, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            rota = gab["decisao_roteamento"]
            manifesto.append({
                "documento_id": caso.id,
                "arquivo": gab["_avaliacao"]["arquivo"],
                "tipo_arquivo": TIPO_ARQUIVO[caso.formato],
                "formato": caso.formato,
                "degradacao": caso.degradacao,
                "canal_origem": caso.canal_origem,
                "tipo_documento": gab["classificacao"]["tipo_documento"],
                "cenario": caso.cenario,
                "nivel_prioridade": gab["classificacao"]["nivel_prioridade"],
                "destino_esperado": rota["destino_principal"],
                "requer_auditoria_humana": str(rota["requer_auditoria_humana"]).lower(),
            })
            print(f"{caso.id}  {caso.cenario:9s} {caso.formato:14s} {caso.degradacao:12s} {arquivo.name}")

    with open(RAIZ / "manifesto.csv", "w", newline="", encoding="utf-8") as saida:
        escritor = csv.DictWriter(saida, fieldnames=list(manifesto[0]))
        escritor.writeheader()
        escritor.writerows(manifesto)

    print(f"\n{len(CASOS)} casos:", dict(Counter(c.cenario for c in CASOS)),
          dict(Counter(c.formato for c in CASOS)))


if __name__ == "__main__":
    main()
