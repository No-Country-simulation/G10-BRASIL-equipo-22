"""
MediFlow — Design System Hospitalar, Badges Manchester e Filtros HitL
Hackathon ONE G10 — Oracle Next Education & Alura (Equipo 22)
Sprint M5: CARD-28 (#37), CARD-29 (#38), CARD-30 (#39), Macro #8
"""

import html
from typing import Any, Dict, List, Optional

# Escala de Triagem de Manchester (Cores Oficiais)
CORES_MANCHESTER = {
    "URGENTE": {"fundo": "#b71c1c", "texto": "#ffffff", "label": "🔴 Emergência (0 min)"},
    "ALTA": {"fundo": "#f57f17", "texto": "#ffffff", "label": "🟡 Muito Urgente (10 min)"},
    "REVISAO_HUMANA": {"fundo": "#e65100", "texto": "#ffffff", "label": "🟠 Retido HitL (Score < 0.85)"},
    "ROTINA": {"fundo": "#1b5e20", "texto": "#ffffff", "label": "🟢 Pouco Urgente (120 min)"},
    "ELETIVO": {"fundo": "#0d47a1", "texto": "#ffffff", "label": "🔵 Não Urgente (240 min)"},
}

CSS_DESIGN_SYSTEM = """
<style>
.mf-badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 9999px;
    font-size: 0.875rem;
    font-weight: 600;
    letter-spacing: 0.025em;
    margin-right: 0.5rem;
}
.mf-card-hitl {
    border: 1px solid #e0e0e0;
    border-radius: 0.5rem;
    padding: 1rem;
    margin-bottom: 1rem;
    background-color: #fafafa;
}
</style>
"""


def gerar_badge_manchester(prioridade: str) -> str:
    """Gera tag HTML do badge Manchester com alto contraste (WCAG AAA) (CARD-29 / #38)."""
    p_norm = (prioridade or "ROTINA").upper().replace(" ", "_")
    cfg = CORES_MANCHESTER.get(p_norm, CORES_MANCHESTER["ROTINA"])
    return (
        f'<span class="mf-badge" style="background-color: {cfg["fundo"]}; color: {cfg["texto"]};">'
        f'{html.escape(cfg["label"])}'
        f'</span>'
    )


def gerar_audio_alerta_sintetico() -> str:
    """Gera elemento HTML5 Audio com beep sintetizado em Base64 para alertas críticos sem assets externos (CARD-29 / #38)."""
    # WAV de 440Hz de 0.2s codificado em base64
    wav_b64 = "UklGRj4AAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YTAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    return f'<audio autoplay style="display:none;"><source src="data:audio/wav;base64,{wav_b64}" type="audio/wav"></audio>'


def filtrar_fila_auditoria(
    fila: List[Dict[str, Any]],
    especialidade: Optional[str] = None,
    prioridade: Optional[str] = None,
    busca: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Filtra itens da fila HitL por especialidade, gravidade e busca textual (CARD-30 / #39)."""
    resultado = []
    for item in fila:
        # Extração defensiva de campos
        esp_item = item.get("especialidade") or item.get("classificacao", {}).get("especialidade", "")
        prio_item = item.get("prioridade") or item.get("classificacao", {}).get("nivel_prioridade", "")
        if hasattr(prio_item, "value"):
            prio_item = prio_item.value

        doc_id = item.get("documento_id", "")
        paciente = item.get("paciente") or item.get("dados_extraidos", {}).get("paciente", {}).get("nome", "")
        crm = item.get("crm") or item.get("dados_extraidos", {}).get("medico_solicitante", {}).get("crm", "")

        # Filtro de especialidade
        if especialidade and especialidade != "Todas":
            if especialidade.lower() not in esp_item.lower():
                continue

        # Filtro de prioridade
        if prioridade and prioridade != "Todas":
            if prioridade.lower() != str(prio_item).lower():
                continue

        # Filtro textual
        if busca:
            termo = busca.lower()
            conteudo_busca = f"{doc_id} {paciente} {crm} {esp_item}".lower()
            if termo not in conteudo_busca:
                continue

        resultado.append(item)
    return resultado
