"""
MediFlow — Componente Visual do Alerta de Plantão (Release 1.3, CARD-06)
Hackathon ONE G10 — Oracle Next Education & Alura (Equipo 22)
Persona Responsável: Fernando Nexus (Fernando Szekut — Frontend/UX & Workflows)

Banner com indicador pulsante e toast quando o agente aciona o plantão. O HTML é montado aqui,
sem Streamlit, para poder ser testado; tudo o que vem do documento ou do modelo é escapado antes
de ir para o unsafe_allow_html.
"""

from __future__ import annotations

import html
from typing import Any, Dict, List, Optional, Tuple

# Vermelho da classificação de Manchester (emergência); texto branco com contraste de 6,6:1 (WCAG AA)
CSS_ALERTA = """
<style>
.mf-alerta { display: flex; gap: 0.9rem; align-items: flex-start; padding: 0.9rem 1.1rem;
  border-radius: 0.5rem; background: #b71c1c; color: #ffffff; line-height: 1.45; }
.mf-alerta strong { font-size: 1.05rem; letter-spacing: 0.02em; }
.mf-pulso { flex: none; width: 0.85rem; height: 0.85rem; margin-top: 0.35rem; border-radius: 50%;
  background: #ffffff; box-shadow: 0 0 0 0 rgba(255, 255, 255, 0.8); animation: mf-pulso 1.4s infinite; }
@keyframes mf-pulso {
  0%   { box-shadow: 0 0 0 0 rgba(255, 255, 255, 0.8); }
  70%  { box-shadow: 0 0 0 0.75rem rgba(255, 255, 255, 0); }
  100% { box-shadow: 0 0 0 0 rgba(255, 255, 255, 0); }
}
@media (prefers-reduced-motion: reduce) { .mf-pulso { animation: none; } }
.mf-entrega { display: inline-block; margin-top: 0.35rem; padding: 0.1rem 0.5rem; border-radius: 0.25rem;
  font-size: 0.85rem; background: rgba(0, 0, 0, 0.25); }
.mf-extra { margin-top: 0.35rem; font-size: 0.9rem; }
</style>
"""

ENTREGA = {
    "sucesso": ("entregue ao plantão", "ok"),
    "sucesso_mock": ("simulado, nenhum webhook configurado", "simulado"),
}


def descrever_entrega(status: Optional[str]) -> Tuple[str, str]:
    """(texto para a tela, classe) a partir do status_entrega do NotificationDispatcher."""
    if status in ENTREGA:
        return ENTREGA[status]
    if not status:
        return ("sem registro de envio", "falha")
    return (f"falhou ({status})", "falha")


def html_alerta_plantao(
    documento_id: str,
    diagnostico: Optional[str],
    status_entrega: Optional[str],
    tambem_em_revisao: bool = False,
) -> str:
    texto_entrega, classe = descrever_entrega(status_entrega)
    extra = (
        '<div class="mf-extra">Também enviado à revisão humana: há dado faltando ou ilegível.</div>'
        if tambem_em_revisao
        else ""
    )
    return (
        CSS_ALERTA
        + '<div class="mf-alerta" role="alert" aria-live="assertive">'
        + '<span class="mf-pulso" aria-hidden="true"></span>'
        + "<div>"
        + f"<strong>PLANTÃO ACIONADO</strong> · {html.escape(documento_id)}<br>"
        + f"{html.escape(diagnostico or 'Quadro crítico agudo')}<br>"
        + f'<span class="mf-entrega mf-{classe}">Webhook: {html.escape(texto_entrega)}</span>'
        + extra
        + "</div></div>"
    )


def mostrar_alerta_plantao(resultado: Any, registro: Optional[Any]) -> None:
    """Banner pulsante + toast para um ResultadoTriagemOutput urgente e seu AlertaClinicoRegistro."""
    import streamlit as st  # type: ignore

    status = registro.status_entrega if registro is not None else None
    diagnostico = resultado.dados_extraidos.diagnostico_principal
    st.markdown(
        html_alerta_plantao(
            resultado.documento_id,
            diagnostico,
            status,
            tambem_em_revisao=resultado.decisao_roteamento.requer_auditoria_humana,
        ),
        unsafe_allow_html=True,
    )
    texto_entrega, _ = descrever_entrega(status)
    st.toast(f"Plantão acionado ({resultado.documento_id}): webhook {texto_entrega}", icon="🚨")


# -----------------------------------------------------------------------------
# Histórico de entregas e reenvio manual (CARD-18)
# -----------------------------------------------------------------------------

def linhas_historico(alertas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Linhas da tabela de histórico, do alerta mais recente para o mais antigo."""
    linhas = []
    for al in reversed(alertas):
        texto_entrega, _ = descrever_entrega(al.get("status"))
        linhas.append({
            "Horário": (al.get("timestamp") or "")[:19].replace("T", " "),
            "Documento": al.get("documento_id"),
            "Canal": al.get("canal"),
            "Entrega": texto_entrega,
            "Latência HTTP (ms)": al.get("latencia_ms"),
            "Tentativas": al.get("tentativas"),
            "Reenvios": al.get("reenvios", 0),
            "ID": al.get("alerta_id"),
        })
    return linhas


def texto_reenvio(resultado: Dict[str, Any]) -> Tuple[str, str]:
    """(nível, texto) para o aviso depois de clicar em reenviar: nível é success, warning ou error."""
    status = resultado.get("status_envio")
    alerta = resultado.get("alerta_id", "?")
    if status == "sucesso":
        return ("success", f"Alerta {alerta} entregue ao plantão no reenvio ({resultado.get('latencia_ms')} ms).")
    if status == "ja_entregue":
        return ("warning", f"Alerta {alerta} já tinha sido entregue; nada foi reenviado.")
    if status == "sem_webhook":
        return ("warning", "Modo simulado: sem WEBHOOK_EMERGENCY_URL não há para onde reenviar.")
    texto_entrega, _ = descrever_entrega(status)
    return ("error", f"Reenvio do alerta {alerta} {texto_entrega}. Resposta: {resultado.get('detalhes') or 'sem resposta'}")


def calcular_metricas_alertas(alertas: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calcula estatísticas de observabilidade para a aba de status de Webhooks (CARD-18)."""
    if not alertas:
        return {
            "total": 0,
            "entregues": 0,
            "simulados": 0,
            "falhas": 0,
            "taxa_sucesso_pct": 100.0,
            "latencia_media_ms": 0.0,
        }

    total = len(alertas)
    entregues = sum(1 for a in alertas if a.get("status") == "sucesso")
    simulados = sum(1 for a in alertas if a.get("status") == "sucesso_mock")
    falhas = total - entregues - simulados
    latencias = [a.get("latencia_ms", 0.0) for a in alertas if a.get("latencia_ms") is not None]
    latencia_media = round(sum(latencias) / len(latencias), 1) if latencias else 0.0
    taxa_sucesso = round(((entregues + simulados) / total) * 100, 1)

    return {
        "total": total,
        "entregues": entregues,
        "simulados": simulados,
        "falhas": falhas,
        "taxa_sucesso_pct": taxa_sucesso,
        "latencia_media_ms": latencia_media,
    }


def renderizar_painel_webhooks_streamlit(dispatcher: Any) -> None:
    """Renderiza a aba completa de histórico de Webhooks e status no Streamlit (CARD-18)."""
    import streamlit as st  # type: ignore

    alertas = [
        {
            "timestamp": r.timestamp,
            "documento_id": r.documento_id,
            "paciente": r.paciente_nome,
            "diagnostico": r.diagnostico,
            "canal": r.canal,
            "status": r.status_entrega,
            "resposta_servidor": r.resposta_servidor,
            "latencia_ms": r.latencia_ms,
            "tentativas": r.tentativas,
            "alerta_id": r.alerta_id,
            "pode_reenviar": dispatcher.pode_reenviar(r),
            "reenvios": r.reenvios,
            "mensagem": r.mensagem,
        }
        for r in dispatcher.historico_alertas
    ]

    st.subheader("📡 Histórico de Entregas & Status de Webhooks em Tempo Real")
    st.caption("Observabilidade SRE de alertas críticos enviados para equipes de plantão hospitalar.")

    if not alertas:
        st.info("Nenhum alerta de plantão foi disparado nesta sessão ainda.")
        return

    # Métricas executivas
    metricas = calcular_metricas_alertas(alertas)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total de Alertas", metricas["total"])
    col2.metric("Entregas Confirmadas", f"{metricas['entregues']} ({metricas['taxa_sucesso_pct']}%)")
    col3.metric("Falhas / Pendentes", metricas["falhas"])
    col4.metric("Latência Média", f"{metricas['latencia_media_ms']} ms")

    st.markdown("### Fila de Disparos")
    st.dataframe(linhas_historico(alertas), use_container_width=True, hide_index=True)

    st.markdown("### Detalhes & Ações de Reenvio Manual")
    for al in reversed(alertas):
        texto_entrega, _ = descrever_entrega(al["status"])
        titulo = f"{al['timestamp'][:19].replace('T', ' ')} · {al['documento_id']} · {texto_entrega}"
        with st.expander(titulo, expanded=al["pode_reenviar"]):
            st.markdown(
                f"Canal: `{al['canal']}` · Latência: **{al['latencia_ms']} ms** · "
                f"Tentativas: `{al['tentativas']}` · Reenvios manuais: `{al['reenvios']}` · ID: `{al['alerta_id']}`"
            )
            st.info(f"Paciente: **{al['paciente']}** | Diagnóstico: **{al['diagnostico']}**")
            st.code(al["mensagem"], language="text")
            if al["status"] not in ("sucesso", "sucesso_mock") and al["resposta_servidor"]:
                st.caption(f"Resposta do servidor: {al['resposta_servidor']}")

            if al["status"] != "sucesso":
                if st.button(
                    "🔄 Reenviar alerta ao plantão",
                    key=f"reenviar_painel_{al['alerta_id']}",
                    disabled=not al["pode_reenviar"],
                    help=None if al["pode_reenviar"] else "Modo simulado: configure WEBHOOK_EMERGENCY_URL para reenviar.",
                ):
                    resultado = dispatcher.reenviar(al["alerta_id"])
                    nivel, texto = texto_reenvio(resultado)
                    getattr(st, nivel)(texto)
                    st.rerun()
