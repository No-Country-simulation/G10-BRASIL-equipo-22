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
from typing import Dict, List

from mediflow_agent import (
    SCENARIO_1_ROUTINE,
    SCENARIO_2_URGENCY_TEP,
    SCENARIO_3_AMBIGUOUS_HITL,
    MediFlowAgentGraph,
)
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
        return resultado

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

    st.set_page_config(page_title="MediFlow — Triagem Clínica & HitL", page_icon="🏥", layout="wide")
    st.title("🏥 MediFlow — Agente Autônomo de Triagem e Roteamento Clínico")
    st.caption("Hackathon ONE G10 (Oracle Next Education & Alura) · Equipo 22: Carlos, Fernando, Helder & Alessandro")

    agent = MediFlowAgentGraph()

    with st.sidebar:
        st.header("⚙️ Telemetria & IA")
        if agent.nvidia_api_key:
            st.success(f"🟢 **NVIDIA NIM Conectado**\n\nModelo: `{agent.nvidia_model}`")
        else:
            st.info("🟡 **Modo SRE Resiliente**\n\nFallback Heurístico Local Ativo (Para ativar a LLM, configure `NVIDIA_API_KEY` no `.env`).")
        st.markdown("---")
        st.caption("☁️ **OCI Always Free:** Bucket `mediflow-documentos-clinicos`")
        st.caption("🛡️ **Equipe 22:** Carlos, Fernando, Helder & Alessandro")

    tab_triagem, tab_hitl, tab_oci = st.tabs([
        "📥 Triagem de Documentos (3 Cenários)",
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
                resultado = agent.run(entrada)
                if resultado.classificacao.nivel_prioridade.value == "Urgente":
                    st.error(f"🚨 PRIORIDADE URGENTE DETECTADA: {resultado.dados_extraidos.diagnostico_principal}")
                elif resultado.decisao_roteamento.requer_auditoria_humana:
                    st.warning("⚠️ DOCUMENTO RETIDO PARA AUDITORIA HUMANA (Score < 0.85)")
                else:
                    st.success(f"✅ APROVADO AUTOMATICAMENTE → {resultado.decisao_roteamento.destino_principal.value}")

                st.json(resultado.to_dict(exclude_none=True))

    with tab_hitl:
        st.subheader("Fila de Revisão Humana (Human-in-the-Loop)")
        st.info("Documentos com score de confiança < 0.85 ou campos vitais ilegíveis aguardam validação do auditor.")
        hitl_sample = agent.run(SCENARIO_3_AMBIGUOUS_HITL)
        st.write(f"**Documento Retido:** `{hitl_sample.documento_id}` | **Score:** `{hitl_sample.classificacao.score_confianca_classificacao}`")
        st.write(f"**Motivo:** {hitl_sample.decisao_roteamento.justificativa_roteamento}")
        crm_fix = st.text_input("Informar CRM validado pelo Auditor:", value="154990-SP")
        if st.button("✅ Aprovar e Liberar Documento Corrigido"):
            st.success(f"Documento {hitl_sample.documento_id} assinado com CRM {crm_fix} e liberado para Farmácia Hospitalar!")

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