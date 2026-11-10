"""Estruturas dos documentos sintéticos, do gabarito e da transcrição de referência."""
import re
from dataclasses import dataclass, field

# Destinos de roteamento (os da especificação do desafio; nomes no estilo do README)
EMERGENCIA = "Fila_Emergencia_Medica"
AUTORIZACOES = "Auditoria_Autorizacoes"
FARMACIA = "Farmacia_Hospitalar"
PRONTUARIO = "Prontuario_Eletronico"
REVISAO = "Fila_Revisao_Humana"
DESTINOS = {EMERGENCIA, AUTORIZACOES, FARMACIA, PRONTUARIO, REVISAO}

CENARIOS = {"rotina", "urgencia", "ambiguo"}
FORMATOS = {"texto", "pdf_digital", "pdf_escaneado", "imagem"}
DEGRADACOES = {"nenhuma", "scan_leve", "scan_pesado", "foto"}

AVISO = "DOCUMENTO FICTÍCIO - dados sintéticos para teste do MediFlow (Equipo 22). Sem validade clínica."

# Marcas dentro de texto manuscrito: {{ILEGIVEL:n}} vira um rabisco de n letras;
# {{RASURA:a>b}} escreve "a" e por cima "b".
TOKEN = re.compile(r"\{\{(ILEGIVEL|RASURA):([^}]*)\}\}")


@dataclass
class Doc:
    """Documento em texto corrido: receita, laudo, relatório de alta, atestado.

    Blocos aceitos:
      ("secao", texto)                     título de seção
      ("par", texto)                       parágrafo com quebra automática
      ("destaque", texto)                  parágrafo em negrito, num quadro
      ("med", nome_e_dose, qtde, uso)      item de receita numerado
      ("tabela", cabecalho, linhas)        resultados de laboratório
      ("linha", texto)                     uma linha sem quebra (manuscrita se o doc for)
      ("impresso", texto)                  linha impressa, mesmo em doc manuscrito
      ("mao", texto, largura)              texto à mão sobre um traço de formulário
    """

    instituicao: str
    endereco: str
    titulo: str
    campos: list[tuple[str, str]]
    blocos: list[tuple]
    assinatura: list[str]
    local_data: str = ""
    tamanho: str = "A4"
    manuscrito: bool = False
    letra: str = "legivel"  # "legivel" | "ruim"
    carimbo: list[str] | None = None
    borrao_no_carimbo: bool = False


@dataclass
class Guia:
    """Guia de solicitação SP/SADT, no espírito do padrão TISS (simplificada)."""

    operadora: str
    registro_ans: str
    numero_guia: str
    carteira: str
    beneficiario: str
    contratado: str
    profissional: str
    conselho: str
    numero_conselho: str
    uf: str
    cbo: str
    carater: str
    data_solicitacao: str
    indicacao_clinica: str
    procedimentos: list[tuple[str, str, str, str]]  # tabela, código, descrição, quantidade


@dataclass
class Caso:
    id: str
    cenario: str
    formato: str
    degradacao: str
    canal_origem: str
    documento: Doc | Guia
    esperado: dict
    motivo: str
    cid_aceitos: list = field(default_factory=list)
    armadilha: str | None = None
    campos_ausentes: list[str] = field(default_factory=list)
    decisao_pendente: str | None = None


def gabarito(*, tipo, especialidade, prioridade, paciente, idade, medico, crm, destino,
             exame=None, exames_solicitados=(), diagnostico=None, cid=None,
             medicamentos=(), auditoria=False, alerta=False, extras=None):
    """Monta a saída esperada no formato do contrato do README (seção 2.3)."""
    dados = {
        "paciente": {"nome": paciente, "idade": idade},
        "medico_solicitante": {"nome": medico, "crm": crm},
        "exame_realizado": exame,
        "exames_solicitados": list(exames_solicitados),
        "diagnostico_principal": diagnostico,
        "cid_sugerido": cid,
        "medicamentos": [
            {"nome": nome, "dosagem": dose, "via": via, "posologia": uso}
            for nome, dose, via, uso in medicamentos
        ],
    }
    if extras:
        dados.update(extras)
    return {
        "classificacao": {
            "tipo_documento": tipo,
            "especialidade": especialidade,
            "nivel_prioridade": prioridade,
        },
        "dados_extraidos": dados,
        "decisao_roteamento": {
            "destino_principal": destino,
            "requer_auditoria_humana": auditoria,
            "notificacao_gerada": {"canal": "Alerta_Plantao_Medico"} if alerta else None,
        },
    }


def limpar(texto: str) -> str:
    """Troca as marcas especiais pelo que um transcritor humano escreveria."""
    return TOKEN.sub(lambda m: "[ilegível]" if m.group(1) == "ILEGIVEL" else "[rasura]", texto)


def transcrever(documento: Doc | Guia) -> str:
    """Texto de referência do documento: entrada dos casos em texto e base da conferência."""
    if isinstance(documento, Guia):
        return _transcrever_guia(documento)
    d = documento
    linhas = [d.instituicao, d.endereco, ""]
    if d.titulo:
        linhas += [d.titulo, ""]
    linhas += [f"{rotulo}: {limpar(valor)}".rstrip() for rotulo, valor in d.campos]
    n_med = 0
    for bloco in d.blocos:
        tipo = bloco[0]
        if tipo == "secao":
            linhas += ["", bloco[1].upper()]
        elif tipo in ("par", "destaque", "linha", "impresso", "mao"):
            linhas.append(limpar(bloco[1]))
        elif tipo == "med":
            n_med += 1
            _, nome, qtde, uso = bloco
            linhas += [f"{n_med}. {nome} - {qtde}", f"   {uso}"]
        elif tipo == "tabela":
            _, cabecalho, corpo = bloco
            linhas.append(" | ".join(cabecalho))
            linhas += [" | ".join(celulas) for celulas in corpo]
    linhas.append("")
    if d.local_data:
        linhas.append(limpar(d.local_data))
    linhas += d.assinatura
    if d.carimbo:
        carimbo = list(d.carimbo)
        if d.borrao_no_carimbo:
            carimbo[-1] = "[ilegível]"
        linhas.append("Carimbo: " + " / ".join(carimbo))
    linhas += ["", AVISO]
    return "\n".join(linhas).strip() + "\n"


def _transcrever_guia(g: Guia) -> str:
    linhas = [
        g.operadora,
        "GUIA DE SERVIÇO PROFISSIONAL / SERVIÇO AUXILIAR DE DIAGNÓSTICO E TERAPIA - SP/SADT",
        f"Registro ANS: {g.registro_ans}",
        f"Nº da guia no prestador: {g.numero_guia}",
        "",
        "DADOS DO BENEFICIÁRIO",
        f"Número da carteira: {g.carteira}",
        f"Nome: {g.beneficiario}",
        "",
        "DADOS DO SOLICITANTE",
        f"Nome do contratado: {g.contratado}",
        f"Nome do profissional solicitante: {g.profissional}",
        f"Conselho profissional: {g.conselho}",
        f"Número no conselho: {g.numero_conselho}".rstrip(),
        f"UF: {g.uf}",
        f"Código CBO: {g.cbo}",
        "",
        "DADOS DA SOLICITAÇÃO",
        f"Caráter do atendimento: {g.carater}",
        f"Data da solicitação: {g.data_solicitacao}",
        f"Indicação clínica: {g.indicacao_clinica}".rstrip(),
        "",
        "PROCEDIMENTOS SOLICITADOS",
        "Tabela | Código | Descrição | Qtde. solicitada",
    ]
    linhas += [" | ".join(p) for p in g.procedimentos]
    linhas += ["", AVISO]
    return "\n".join(linhas) + "\n"
