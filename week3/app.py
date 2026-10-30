"""
MediFlow — Painel Gráfico Interativo Streamlit (Release 1.3)
Hackathon ONE G10 — Oracle Next Education & Alura (Equipo 22)

Squad:
  - Carlos Magno (Tech Lead, SRE/DevOps, IA & Python Core)
  - Fernando Szekut (Agent Integration, Webhooks & Frontend/UX)
  - Helder (Atlas Data — OCI Object Storage & SQLite Audit)
  - Alessandro (Marcus Builder — Backend FastAPI & QA)

Execução:
  streamlit run week3/app.py --server.port 8501
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
import streamlit as st  # type: ignore

# Ajuste de path para o projeto raiz
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from mediflow_schemas import (
    DocumentoClinicoInput,
    DestinoRoteamentoEnum,
    NivelPrioridadeEnum,
    TipoArquivoEnum,
)
from week3.agent import (
    MediFlowStateGraphAgent,
    SCENARIO_1_ROUTINE,
    SCENARIO_2_URGENCY_TEP,
    SCENARIO_3_AMBIGUOUS_HITL,
)
from week3.notifications import NotificationDispatcher
from week3.storage import OCIStorageServiceV3
from week3.ui_alertas import descrever_entrega, mostrar_alerta_plantao


# Inicialização segura de estado no Streamlit
@st.cache_resource
def get_services():
    storage = OCIStorageServiceV3()
    dispatcher = NotificationDispatcher()
    agent = MediFlowStateGraphAgent(
        storage_service=storage,
        notification_dispatcher=dispatcher,
    )
    return storage, dispatcher, agent


def main():
    st.set_page_config(
        page_title="MediFlow Release 1.3 — Triagem Clínica & LangGraph",
        page_icon="🏥",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    storage, dispatcher, agent = get_services()

    # Cabeçalho Principal
    st.title("🏥 MediFlow — Release 1.3: Grafo de Decisão Condicional & Workflows")
    st.caption("Hackathon ONE G10 (Oracle Next Education & Alura) · Equipo 22")

    # Barra Lateral
    with st.sidebar:
        st.header("⚙️ Status do Sistema")
        if agent.nvidia_api_key:
            st.success(f"🟢 **NVIDIA NIM Conectado**\n\nModelo: `{agent.nvidia_model}`")
        else:
            st.info("🟡 **Modo SRE Resiliente Ativo**\n\nMotor Heurístico Local de Contingência (Zero Downtime)")

        st.markdown("---")
        st.subheader("👥 Squad Equipo 22")
        st.markdown(
            "• **Carlos Magno** *(Tech Lead & SRE)*  \n"
            "• **Fernando Szekut** *(Agent Workflows & Front)*  \n"
            "• **Helder** *(OCI & SQLite Audit)*  \n"
            "• **Alessandro** *(FastAPI Backend & QA)*"
        )
        st.markdown("---")
        compliance = storage.check_always_free_compliance()
        st.caption(f"☁️ **OCI Storage:** `{storage.bucket_name}`")
        st.caption(f"🛡️ **Status Camada Gratuita:** {compliance['tier']}")

    # Abas da Interface
    tab_triagem, tab_hitl, tab_webhooks, tab_grafo, tab_dados = st.tabs([
        "📥 Triagem Clínica Interativa",
        "👩‍⚕️ Auditoria Humana (HitL)",
        "🚨 Alertas & Webhooks (Fernando Nexus)",
        "🕸️ Topologia do Grafo (StateGraph)",
        "☁️ OCI Storage & Log SQLite (Atlas Data)",
    ])

    # -------------------------------------------------------------------------
    # ABA 1: Triagem Clínica Interativa
    # -------------------------------------------------------------------------
    with tab_triagem:
        st.subheader("Simulador de Triagem Médica Automatizada (LangGraph)")
        st.write("Selecione um dos 3 cenários clínicos homologados ou digite um novo caso:")

        col_preset, col_canal = st.columns([2, 1])
        with col_preset:
            preset = st.selectbox(
                "Cenário de Teste:",
                [
                    "Cenário 1 — Fluxo Padrão Aprovado (Receituário Amoxicilina)",
                    "Cenário 2 — Urgência Médica Crítica (TEP Agudo / Webhook)",
                    "Cenário 3 — Caso Ambíguo / Rasura (Retenção Human-in-the-Loop)",
                ],
            )
        with col_canal:
            canal = st.selectbox(
                "Canal Hospitalar de Origem:",
                ["Ambulatorio", "Pronto_Socorro", "Radiologia", "Internacao"],
            )

        if "Cenário 1" in preset:
            default_doc = SCENARIO_1_ROUTINE
        elif "Cenário 2" in preset:
            default_doc = SCENARIO_2_URGENCY_TEP
        else:
            default_doc = SCENARIO_3_AMBIGUOUS_HITL

        col_input, col_output = st.columns([1, 1])

        with col_input:
            doc_id = st.text_input("ID do Documento:", value=default_doc.documento_id)
            texto = st.text_area("Texto do Documento Clínico:", value=default_doc.documento_texto, height=180)
            btn_run = st.button("⚡ Executar Triagem no Grafo", type="primary", use_container_width=True)

        with col_output:
            if btn_run:
                payload = DocumentoClinicoInput(
                    documento_id=doc_id,
                    tipo_arquivo=TipoArquivoEnum.TEXTO,
                    documento_texto=texto,
                    canal_origem=canal,
                )
                with st.spinner("Executando nós do LangGraph StateGraph..."):
                    resultado = agent.run(payload)

                prioridade = resultado.classificacao.nivel_prioridade.value
                confianca = resultado.classificacao.score_confianca_classificacao

                if prioridade == "Urgente":
                    registro = next(
                        (a for a in reversed(dispatcher.historico_alertas) if a.documento_id == resultado.documento_id),
                        None,
                    )
                    mostrar_alerta_plantao(resultado, registro)
                elif resultado.decisao_roteamento.requer_auditoria_humana:
                    st.warning(f"⚠️ **DOCUMENTO RETIDO PARA AUDITORIA HUMANA (HitL)**\n\nScore de Confiança: **{confianca:.2f}** (< 0.85)")
                else:
                    st.success(f"✅ **DOCUMENTO APROVADO AUTOMATICAMENTE**\n\nEncaminhado para: **{resultado.decisao_roteamento.destino_principal.value}**")

                # Métricas em colunas
                m1, m2, m3 = st.columns(3)
                m1.metric("Tipo Documento", resultado.classificacao.tipo_documento)
                m2.metric("Especialidade", resultado.classificacao.especialidade)
                m3.metric("Score Confiança", f"{confianca * 100:.1f}%")

                st.markdown(f"**Destino:** `{resultado.decisao_roteamento.destino_principal.value}`")
                st.markdown(f"**Justificativa:** {resultado.decisao_roteamento.justificativa_roteamento}")
                st.markdown(f"**Caminho OCI:** `{resultado.armazenamento_oci.caminho_objeto}`")

                with st.expander("🔍 Ver JSON Estruturado Completo"):
                    st.json(resultado.to_dict(exclude_none=True))

    # -------------------------------------------------------------------------
    # ABA 2: Painel de Auditoria Humana (HitL)
    # -------------------------------------------------------------------------
    with tab_hitl:
        st.subheader("👩‍⚕️ Painel Clínico de Human-in-the-Loop (HitL)")
        st.info("Documentos com score de confiança inferior a 85% ou divergências cadastrais são retidos preventivamente para homologação do médico auditor.")

        # Amostra com Cenário 3
        st.markdown("### Exemplo de Documento em Análise na Fila:")
        col_hitl_left, col_hitl_right = st.columns([1, 1])

        with col_hitl_left:
            st.warning("⚠️ **Documento: DOC-CLIN-2026-5503** (Retido preventivamente)")
            st.markdown("- **Paciente:** Roberto F...")
            st.markdown("- **Prescrição:** Metoprolol dosagem borrada ?? mg uso contínuo")
            st.markdown("- **Motivo da Retenção:** Ausência de CRM válido e dosagem ilegível.")

        with col_hitl_right:
            crm_corrigido = st.text_input("CRM Validado pelo Auditor Médico:", value="184930-SP")
            destino_aprovado = st.selectbox("Destino pós-aprovação:", ["Farmacia_Hospitalar", "Prontuario_Eletronico_PEP"])

            if st.button("✅ Aprovar e Liberar Documento", type="primary"):
                storage.update_audit_status(
                    documento_id="DOC-CLIN-2026-5503",
                    novo_status="aprovado_pos_auditoria",
                    crm_corrigido=crm_corrigido,
                    novo_destino=destino_aprovado,
                )
                st.success(f"Documento DOC-CLIN-2026-5503 aprovado com CRM {crm_corrigido} e liberado para {destino_aprovado}!")

    # -------------------------------------------------------------------------
    # ABA 3: Alertas & Webhooks em Tempo Real (Fernando Nexus)
    # -------------------------------------------------------------------------
    with tab_webhooks:
        st.subheader("🚨 Despachador de Alertas em Tempo Real & Webhooks")
        st.write("Responsável: **Fernando Szekut (Fernando Nexus)** · Módulo `NotificationDispatcher`")

        if dispatcher.mock_mode:
            st.warning("**Modo simulado:** sem `WEBHOOK_EMERGENCY_URL`, os alertas abaixo não saíram do MediFlow.")

        alertas = dispatcher.get_recent_alerts(limit=20)
        if alertas:
            falhas = [al for al in alertas if al["status"] not in ("sucesso", "sucesso_mock")]
            st.success(f"Total de alertas emitidos nesta sessão: **{len(alertas)}**")
            if falhas:
                st.error(f"**{len(falhas)} alerta(s) não entregue(s) ao plantão.** Veja a resposta do servidor abaixo.")
            for idx, al in enumerate(alertas):
                texto_entrega, _ = descrever_entrega(al["status"])
                with st.container():
                    st.markdown(
                        f"**Alerta #{idx+1}** · `{al['timestamp']}` · Canal: `{al['canal']}` · "
                        f"Webhook: **{texto_entrega}** · {al['latencia_ms']} ms · {al['tentativas']} tentativa(s)"
                    )
                    st.info(f"Paciente: **{al['paciente']}** | Diagnóstico: **{al['diagnostico']}**")
                    st.code(al["mensagem"], language="text")
                    if al["status"] not in ("sucesso", "sucesso_mock") and al["resposta_servidor"]:
                        st.caption(f"Resposta do servidor: {al['resposta_servidor']}")
                    st.markdown("---")
        else:
            st.info("Nenhum alerta de emergência médica disparado ainda. Execute o **Cenário 2 (TEP Agudo)** para disparar um alerta!")

    # -------------------------------------------------------------------------
    # ABA 4: Topologia do Grafo (StateGraph)
    # -------------------------------------------------------------------------
    with tab_grafo:
        st.subheader("🕸️ Topologia do StateGraph compilado (LangGraph)")
        st.write("Arquiteto Responsável: **Carlos Magno (Arquiteto Carlos Vance)**")

        mermaid_code = agent.get_graph_mermaid()
        st.code(mermaid_code, language="mermaid")

        st.markdown("### Arquitetura de Estados e Transições:")
        st.markdown(
            "1. **`ingestor_node`**: Recebe o payload e persiste backup bruto em `recebidos/`\n"
            "2. **`classifier_extractor_node`**: Invoca o NVIDIA NIM Llama 3.2 11B Vision (com fallback SRE heurístico)\n"
            "3. **`validator_sre_check_node`**: Aplica validação de esquemas Pydantic v2 e regras de confiabilidade clínica\n"
            "4. **`decide_route` (Aresta Condicional)**: Desvia para `emergency_route`, `routine_route` ou `hitl_route`\n"
            "5. **`oci_persistence_node`**: Realiza a segregação dinâmica no bucket Always Free e registra log transacional no SQLite"
        )

    # -------------------------------------------------------------------------
    # ABA 5: OCI Storage & Log SQLite (Atlas Data)
    # -------------------------------------------------------------------------
    with tab_dados:
        st.subheader("☁️ Persistência OCI Always Free & Histórico Transacional SQLite")
        st.write("Engenheiro Responsável: **Helder (Atlas Data)**")

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### Conformidade com a Camada Gratuita:")
            st.json(storage.check_always_free_compliance())

        with c2:
            st.markdown("#### Estrutura de Pastas Segregadas:")
            st.markdown(
                "- `recebidos/` — Ingestão bruta\n"
                "- `processados/rotina/{especialidade}/` — Rotina aprovada\n"
                "- `processados/urgentes/{especialidade}/` — Emergências médicas\n"
                "- `auditoria_humana/{especialidade}/` — Casos retidos para HitL"
            )

        st.markdown("#### Últimos Registros na Tabela SQLite `triagem_audit_log`:")
        historico = storage.get_audit_history(limit=20)
        if historico:
            st.dataframe(historico, use_container_width=True)
        else:
            st.info("Ainda não há registros de auditoria no SQLite local. Execute uma triagem na Aba 1 para gravar o primeiro registro.")


if __name__ == "__main__":
    main()

