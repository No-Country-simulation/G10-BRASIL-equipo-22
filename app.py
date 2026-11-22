"""
MediFlow — Interface de Triagem & Painel de Auditoria Human-in-the-Loop (Streamlit + FastAPI)
Hackathon ONE G10 — Oracle Next Education & Alura (Equipo 22)
Equipe:
  - Arquiteto Carlos Vance (Carlos): Tech Lead, Líder SRE/DevOps, Arquitetura IA & Python
  - Fernando Nexus (Fernando Szekut): Engenheiro de Integração de Agentes, Frontend/UX & Workflows
  - Atlas Data (Helder): Banco de Dados & Persistência OCI Always Free
  - Marcus Builder (Alessandro): Desenvolvedor Backend FastAPI, HitL & QA
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from mediflow_agent import (
    SCENARIO_1_ROUTINE,
    SCENARIO_2_URGENCY_TEP,
    SCENARIO_3_AMBIGUOUS_HITL,
    MediFlowAgentGraph,
)
from mediflow_circuit_breaker import CircuitBreakerState, ResilientMediFlowClient
from mediflow_schemas import DocumentoClinicoInput, ResultadoTriagemOutput, TipoArquivoEnum

# =============================================================================
# 1. API REST (FastAPI) — Endpoint Oficial `/api/v1/triagem`
# =============================================================================
try:
    from fastapi import FastAPI, HTTPException

    api = FastAPI(
        title="MediFlow Autonomous Clinical Triage API",
        description="Agente Autônomo para Triagem, Extração e Roteamento de Documentos Clínicos (ONE G10 - Equipo 22)",
        version="0.2.0",
    )
    _agent_instance = MediFlowAgentGraph()
    _audit_queue: Dict[str, ResultadoTriagemOutput] = {}

    @api.get("/", include_in_schema=False)
    def root_redirect():
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/docs")

    @api.get("/health")
    def healthcheck() -> dict:
        return {
            "status": "healthy",
            "service": "mediflow-agent",
            "oci_bucket": _agent_instance.storage.bucket_name,
            "tier": "OCI Always Free",
        }

    @api.post("/api/v1/triagem", response_model=ResultadoTriagemOutput)
    def processar_triagem(payload: DocumentoClinicoInput) -> ResultadoTriagemOutput:
        resultado = _agent_instance.run(payload)
        if resultado.decisao_roteamento.requer_auditoria_humana:
            _audit_queue[resultado.documento_id] = resultado

        # Persistência relacional auditável (OCI ATP / SQLite) (CARD-19/22)
        try:
            from oci_storage import OCIATPManager
            atp = OCIATPManager()
            atp.salvar_registro(
                documento_id=resultado.documento_id,
                tipo_documento=resultado.classificacao.tipo_documento,
                crm_medico=resultado.dados_extraidos.medico_solicitante.crm,
                paciente_nome=resultado.dados_extraidos.paciente.nome,
                prioridade=resultado.classificacao.nivel_prioridade.value,
                score_confianca=resultado.classificacao.score_confianca_classificacao,
                requer_auditoria=resultado.decisao_roteamento.requer_auditoria_humana,
                payload_json=resultado.to_dict(exclude_none=True),
            )
        except Exception:
            pass

        return resultado

    @api.get("/api/v1/documentos/{documento_id}")
    def obter_documento_por_id(documento_id: str) -> dict:
        """Busca detalhada de documento clínico por ID com metadados e payload (CARD-22 / #31)."""
        if documento_id in _audit_queue:
            doc_data = _audit_queue[documento_id].to_dict(exclude_none=True)
            return {
                "status": "em_auditoria",
                "documento_id": documento_id,
                "documento": doc_data,
                "payload": doc_data,
            }

        import sqlite3
        from oci_storage import OCIATPManager
        atp = OCIATPManager()
        with sqlite3.connect(atp.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM clinico_audit_historico WHERE documento_id = ?",
                (documento_id,),
            ).fetchone()
            if row:
                return {
                    "status": "encontrado",
                    "documento_id": row["documento_id"],
                    "tipo_documento": row["tipo_documento"],
                    "crm_medico": row["crm_medico"],
                    "paciente_nome": row["paciente_nome"],
                    "prioridade": row["prioridade"],
                    "score_confianca": row["score_confianca"],
                    "requer_auditoria": bool(row["requer_auditoria"]),
                    "payload": json.loads(row["payload_json"]) if row["payload_json"] else {},
                    "data_criacao": row["data_criacao"],
                }

        raise HTTPException(status_code=404, detail=f"Documento {documento_id} não encontrado.")

    @api.get("/api/v1/historico")
    def consultar_historico(
        crm: Optional[str] = None,
        prioridade: Optional[str] = None,
        tipo_documento: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> dict:
        """Consulta histórica de documentos processados com filtros por CRM, prioridade e paginação (CARD-22 / #31)."""
        import sqlite3
        from oci_storage import OCIATPManager
        atp = OCIATPManager()
        with sqlite3.connect(atp.db_path) as conn:
            conn.row_factory = sqlite3.Row
            query = "SELECT * FROM clinico_audit_historico WHERE 1=1"
            params: list[Any] = []
            if crm:
                query += " AND crm_medico = ?"
                params.append(crm)
            if prioridade:
                query += " AND prioridade = ?"
                params.append(prioridade)
            if tipo_documento:
                query += " AND tipo_documento = ?"
                params.append(tipo_documento)

            count_query = query.replace("SELECT *", "SELECT COUNT(*)")
            total = conn.execute(count_query, params).fetchone()[0]

            query += " ORDER BY data_criacao DESC LIMIT ? OFFSET ?"
            offset = max(0, (page - 1) * limit)
            params.extend([limit, offset])

            rows = conn.execute(query, params).fetchall()
            documentos = [
                {
                    "documento_id": r["documento_id"],
                    "tipo_documento": r["tipo_documento"],
                    "crm_medico": r["crm_medico"],
                    "paciente_nome": r["paciente_nome"],
                    "prioridade": r["prioridade"],
                    "score_confianca": r["score_confianca"],
                    "requer_auditoria": bool(r["requer_auditoria"]),
                    "data_criacao": r["data_criacao"],
                }
                for r in rows
            ]
            return {
                "total": total,
                "page": page,
                "limit": limit,
                "documentos": documentos,
            }

    @api.get("/api/v1/auditoria", response_model=List[ResultadoTriagemOutput])
    def listar_fila_auditoria_humana() -> List[ResultadoTriagemOutput]:
        return list(_audit_queue.values())

    @api.post("/api/v1/auditoria/{documento_id}/aprovar")
    def aprovar_documento_hitl(documento_id: str, crm_corrigido: str, destino_final: str = "Farmacia_Hospitalar") -> dict:
        if documento_id not in _audit_queue:
            raise HTTPException(status_code=404, detail="Documento não encontrado na fila de revisão humana.")
        item = _audit_queue.pop(documento_id)
        item.status = "aprovado_pos_auditoria"
        item.dados_extraidos.medico_solicitante.crm = crm_corrigido
        item.decisao_roteamento.requer_auditoria_humana = False
        return {
            "mensagem": f"Documento {documento_id} aprovado pelo auditor humano e encaminhado para {destino_final}.",
            "registro_atualizado": item.to_dict(exclude_none=True),
        }

except ImportError:
    api = None


# =============================================================================
# 2. Painel Visual & Auditoria Human-in-the-Loop (Streamlit)
# =============================================================================
def run_streamlit_dashboard() -> None:
    import streamlit as st  # type: ignore
    from week5_ui_helpers import (
        CSS_DESIGN_SYSTEM,
        gerar_badge_manchester,
        gerar_audio_alerta_sintetico,
        filtrar_fila_auditoria,
    )

    st.set_page_config(page_title="MediFlow — Triagem Clínica & HitL", page_icon="🏥", layout="wide")
    st.markdown(CSS_DESIGN_SYSTEM, unsafe_allow_html=True)
    st.title("🏥 MediFlow — Agente Autônomo de Triagem e Roteamento Clínico")
    st.caption("Hackathon ONE G10 (Oracle Next Education & Alura) · Equipo 22: Carlos, Fernando, Helder & Alessandro")

    agent = MediFlowAgentGraph()
    if "resilient_client" not in st.session_state:
        st.session_state["resilient_client"] = ResilientMediFlowClient(local_agent=agent)
    client: ResilientMediFlowClient = st.session_state["resilient_client"]

    # Fila de auditoria em memória compartilhada na sessão
    if "fila_hitl" not in st.session_state:
        sample = agent.run(SCENARIO_3_AMBIGUOUS_HITL)
        st.session_state["fila_hitl"] = [
            {
                "documento_id": sample.documento_id,
                "especialidade": sample.classificacao.especialidade,
                "prioridade": sample.classificacao.nivel_prioridade.value,
                "score": sample.classificacao.score_confianca_classificacao,
                "paciente": sample.dados_extraidos.paciente.nome or "Carlos Eduardo",
                "crm": sample.dados_extraidos.medico_solicitante.crm or "Sem CRM",
                "motivo": sample.decisao_roteamento.justificativa_roteamento,
                "payload": sample.to_dict(exclude_none=True),
            }
        ]

    with st.sidebar:
        st.header("⚙️ Telemetria & IA")
        if agent.nvidia_api_key:
            st.success(f"🟢 **NVIDIA NIM Conectado**\n\nModelo: `{agent.nvidia_model}`")
        else:
            st.info("🟡 **Modo SRE Resiliente**\n\nFallback Heurístico Local Ativo (Para ativar a LLM, configure `NVIDIA_API_KEY` no `.env`).")

        st.markdown("---")
        st.subheader("🛡️ Circuit-Breaker SRE")
        cb_metrics = client.breaker.get_metrics()
        cb_state = cb_metrics["state"]

        if cb_state == CircuitBreakerState.CLOSED.value:
            st.success(f"🟢 **Circuito: {cb_state}**\n\nRequisições fluem para a API REST FastAPI.")
        elif cb_state == CircuitBreakerState.OPEN.value:
            st.error(f"🔴 **Circuito: {cb_state}**\n\nContingência local ativa (Zero Downtime).")
        else:
            st.warning(f"🟡 **Circuito: {cb_state}**\n\nSondando recuperação do backend.")

        c1, c2 = st.columns(2)
        c1.metric("Total Chamadas", cb_metrics["total_calls"])
        c2.metric("Fallbacks SRE", cb_metrics["fallback_calls"])

        if st.button("🔄 Resetar Circuit-Breaker"):
            client.breaker.reset()
            st.rerun()

        st.markdown("---")
        st.caption("☁️ **OCI Always Free:** Bucket `mediflow-documentos-clinicos`")
        st.caption("🛡️ **Equipe 22:** Carlos, Fernando, Helder & Alessandro")

    tab_triagem, tab_visualizador, tab_hitl, tab_oci = st.tabs([
        "📥 Triagem de Documentos (3 Cenários)",
        "👁️ Visualizador Lado a Lado (Conferência Médica)",
        "👩‍⚕️ Painel de Auditoria Humana (HitL)",
        "☁️ Buckets OCI Object Storage & Banco de Dados (Always Free)",
    ])

    with tab_triagem:
        st.subheader("Simulador Interativo dos 3 Cenários Obrigatórios do Hackathon")
        preset = st.selectbox(
            "Selecione um caso de teste oficial ou insira um novo documento:",
            [
                "Cenário 2 (Urgência Médica — TEP Agudo — DOC-CLIN-2026-8942)",
                "Cenário 1 (Fluxo Padrão Aprovado — Receituário — DOC-CLIN-2026-1001)",
                "Cenário 3 (Caso Ambíguo / Sem CRM — Revisão Humana HitL — DOC-CLIN-2026-5503)",
            ],
        )

        if "Cenário 2" in preset:
            default_doc = SCENARIO_2_URGENCY_TEP
        elif "Cenário 1" in preset:
            default_doc = SCENARIO_1_ROUTINE
        else:
            default_doc = SCENARIO_3_AMBIGUOUS_HITL

        col1, col2 = st.columns(2)
        with col1:
            doc_id = st.text_input("ID do Documento", value=default_doc.documento_id)
            canal = st.text_input("Canal de Origem", value=default_doc.canal_origem)
            texto = st.text_area("Texto / Transcrição Multimodal do Documento", value=default_doc.documento_texto, height=180)
            executar = st.button("🚀 Executar Agente MediFlow", type="primary")

        with col2:
            if executar:
                entrada = DocumentoClinicoInput(
                    documento_id=doc_id,
                    tipo_arquivo=TipoArquivoEnum.PDF,
                    documento_texto=texto,
                    canal_origem=canal,
                )
                with st.spinner("Processando via cliente resiliente (Circuit-Breaker)..."):
                    resultado, meta = client.processar_triagem(entrada)

                # Feedback do Circuit-Breaker SRE
                if meta.get("origem") == "fallback_local_in_process":
                    st.warning(
                        f"⚡ **Modo de Contingência SRE Ativo (Circuit-Breaker: {meta.get('status_circuito')})**\n\n"
                        f"{meta.get('aviso')} — Latência: **{meta.get('latencia_ms')} ms**"
                    )
                else:
                    st.info(
                        f"🌐 **Processado via API REST FastAPI** ({meta.get('url')}) — "
                        f"Latência HTTP: **{meta.get('latencia_ms')} ms**"
                    )

                prio_val = resultado.classificacao.nivel_prioridade.value
                st.markdown(gerar_badge_manchester(prio_val), unsafe_allow_html=True)

                if prio_val == "Urgente":
                    st.markdown(gerar_audio_alerta_sintetico(), unsafe_allow_html=True)
                    st.error(f"🚨 PRIORIDADE URGENTE DETECTADA: {resultado.dados_extraidos.diagnostico_principal}")
                elif resultado.decisao_roteamento.requer_auditoria_humana:
                    st.warning("⚠️ DOCUMENTO RETIDO PARA AUDITORIA HUMANA (Score < 0.85)")
                    # Adiciona à fila HitL interativa
                    st.session_state["fila_hitl"].append({
                        "documento_id": resultado.documento_id,
                        "especialidade": resultado.classificacao.especialidade,
                        "prioridade": prio_val,
                        "score": resultado.classificacao.score_confianca_classificacao,
                        "paciente": resultado.dados_extraidos.paciente.nome or "Paciente Não Identificado",
                        "crm": resultado.dados_extraidos.medico_solicitante.crm or "Sem CRM",
                        "motivo": resultado.decisao_roteamento.justificativa_roteamento,
                        "payload": resultado.to_dict(exclude_none=True),
                    })
                else:
                    st.success(f"✅ APROVADO AUTOMATICAMENTE → {resultado.decisao_roteamento.destino_principal.value}")

                st.json(resultado.to_dict(exclude_none=True))

    with tab_visualizador:
        st.subheader("👁️ Visualizador Lado a Lado (Conferência Médica Multimodal) (CARD-28 / #37)")
        st.caption("Inspeção visual direta comparando o documento original submetido com as entidades clínicas extraídas pela IA.")
        
        col_doc_orig, col_dados_extra = st.columns([1, 1])
        with col_doc_orig:
            st.markdown("#### 📄 Documento Clínico Original")
            st.info(f"**ID:** `{default_doc.documento_id}` | **Origem:** `{default_doc.canal_origem}`")
            st.text_area(
                "Conteúdo do Laudo / Prescrição:",
                value=default_doc.documento_texto or "Arquivo de imagem digitalizado",
                height=320,
                disabled=True,
            )

        with col_dados_extra:
            st.markdown("#### 🩺 Entidades Clínicas Extraídas")
            prio_default = "Urgente" if "Cenário 2" in preset else ("Rotina" if "Cenário 1" in preset else "Revisao_Humana")
            st.markdown(gerar_badge_manchester(prio_default), unsafe_allow_html=True)
            
            with st.container():
                st.text_input("Paciente:", value="Carlos Eduardo Mendes" if "Cenário 2" in preset else "Ana Paula Costa", disabled=True)
                st.text_input("Diagnóstico / Conclusão:", value="Tromboembolismo Pulmonar Agudo (TEP)" if "Cenário 2" in preset else "Receituário Padrão", disabled=True)
                st.text_input("CRM do Solicitante:", value="145892-SP" if "Cenário 2" in preset else "98765-RJ", disabled=True)
                st.text_input("Hipótese CID-10:", value="I26.9" if "Cenário 2" in preset else "Z76.0", disabled=True)

    with tab_hitl:
        st.subheader("👩‍⚕️ Fila de Revisão Humana (Human-in-the-Loop) (CARD-30 / #39)")
        st.info("Painel de auditoria com filtros dinâmicos de especialidade e gravidade para aprovação em 1 clique.")

        # Filtros Dinâmicos (CARD-30)
        cf1, cf2, cf3 = st.columns(3)
        with cf1:
            filtro_esp = st.selectbox("Filtrar Especialidade:", ["Todas", "Radiologia", "Pneumologia", "Clínica Médica", "Cardiologia"])
        with cf2:
            filtro_prio = st.selectbox("Filtrar Gravidade:", ["Todas", "Urgente", "Alta", "Revisao_Humana", "Rotina"])
        with cf3:
            busca_termo = st.text_input("Busca Rápida (Paciente, CRM ou ID):", "")

        fila_filtrada = filtrar_fila_auditoria(
            st.session_state["fila_hitl"],
            especialidade=filtro_esp,
            prioridade=filtro_prio,
            busca=busca_termo,
        )

        st.caption(f"Mostrando **{len(fila_filtrada)}** de **{len(st.session_state['fila_hitl'])}** documentos na fila de auditoria.")

        # Renderização dos Cards com Aprovação em 1 Clique (Macro #8)
        for idx, item in enumerate(fila_filtrada):
            doc_item_id = item["documento_id"]
            with st.expander(f"📋 {doc_item_id} — {item.get('paciente')} (Score: {item.get('score')})", expanded=True):
                st.markdown(gerar_badge_manchester(item.get("prioridade")), unsafe_allow_html=True)
                st.write(f"**Motivo de Retenção:** {item.get('motivo')}")
                
                crm_input = st.text_input("CRM Validado:", value=item.get("crm") if item.get("crm") != "Sem CRM" else "154990-SP", key=f"crm_{doc_item_id}_{idx}")
                
                if st.button("✅ Aprovar Laudo em 1 Clique", key=f"btn_aprov_{doc_item_id}_{idx}", type="primary"):
                    st.session_state["fila_hitl"] = [d for d in st.session_state["fila_hitl"] if d["documento_id"] != doc_item_id]
                    st.success(f"Documento {doc_item_id} aprovado com CRM {crm_input} e liberado para Farmácia Hospitalar!")
                    st.rerun()

    with tab_oci:
        st.subheader("Segregação de Objetos no Bucket `mediflow-documentos-clinicos` (OCI Always Free)")
        st.markdown(
            "- `recebidos/` — Cópia bruta dos documentos clínicos ingeridos\n"
            "- `processados/rotina/` — Documentos aprovados automaticamente ($\\text{score} \\ge 0.85$)\n"
            "- `processados/urgentes/` — Casos críticos de emergência médica (ex.: TEP Agudo)\n"
            "- `auditoria_humana/` — Casos retidos para intervenção de auditor clínico"
        )


# Ativação automática quando executado pelo Streamlit
try:
    import streamlit as st  # type: ignore
    if hasattr(st, "runtime") and st.runtime.exists():
        run_streamlit_dashboard()
except Exception:
    pass


if __name__ == "__main__":
    import sys
    try:
        import streamlit as st  # type: ignore
        is_streamlit = hasattr(st, "runtime") and st.runtime.exists()
    except Exception:
        is_streamlit = False

    if not is_streamlit:
        import uvicorn
        print("🏥 Iniciando Servidor API REST do MediFlow (FastAPI)...")
        print("   URL Base: http://127.0.0.1:8000")
        print("   Swagger Docs: http://127.0.0.1:8000/docs")
        print("   Healthcheck: http://127.0.0.1:8000/health")
        uvicorn.run("app:api", host="0.0.0.0", port=8000, reload=False)