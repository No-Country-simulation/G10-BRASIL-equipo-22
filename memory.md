# MediFlow — Project Memory & Tracking Document
**Project:** MediFlow — Agente Autônomo para Triagem, Extração e Roteamento de Documentos Clínicos  
**Initiative:** Hackathon ONE G10 — Oracle Next Education & Alura  
**Team / Squad:** Equipo 22  
**Current Milestone:** Core Specification v0.1  
**Last Updated:** 2026-10-23  

---

## 1. Project Context & Vision

### 1.1 Business & Clinical Context
HealthTech / Hospital Management / Health Insurance & Clinics handle thousands of heterogeneous clinical documents daily:
- Medical prescriptions (*Receituários Médicos*)
- Imaging and Laboratory diagnostic reports (*Laudos de Exames*)
- Authorization guides (*Guias TISS/TUSS*)
- Supplementary test requests (*Pedidos de Exames Complementares*)
- Discharge/Hospitalization summaries (*Relatórios de Alta/Internação*)
- Medical certificates (*Atestados Médicos*)

**Core Pain Points:**
1. Manual review causes administrative overhead and transcription errors.
2. Delays in processing critical diagnostic findings (e.g., Acute Pulmonary Embolism) endanger patient lives.
3. Glosas (denials of reimbursement) and authorization delays generate billions in losses for healthcare providers.

### 1.2 System Purpose & Value Proposition
MediFlow is an intelligent autonomous agent that:
- Ingests multi-format clinical documents (digital/scanned PDF, images, raw text, JSON).
- Employs multimodal LLMs (e.g., Google Gemini, OpenAI GPT-4o, Claude) to classify documents and extract structured clinical entities.
- Calculates an extraction confidence score and detects clinical urgencies.
- Runs an agentic conditional decision graph (LangGraph / conditional pipelines) to route documents to appropriate destinations.
- Segregates and stores data into Oracle Cloud Infrastructure (OCI) Object Storage (Always Free tier).
- Integrates Human-in-the-Loop (HitL) auditor queues for ambiguous or low-confidence documents.

---

## 2. Technical Stack & Architecture Decisions

| Domain | Technology / Decision | Justification |
| :--- | :--- | :--- |
| **Multimodal LLM** | Google Gemini (primary/ONE curriculum), OpenAI / Claude (fallback) | Native multimodal document reasoning, clinical text interpretation, low latency. |
| **Agent Orchestration** | LangGraph / StateGraph (Python) | Deterministic state transitions, conditional edges, cycle handling, and Human-in-the-Loop interruptions. |
| **Data Validation** | Pydantic v2 / JSON Schema | Strict clinical entity typing, schema compliance, field validation. |
| **Cloud Storage** | OCI Object Storage (Always Free Tier) | Mandatory requirement; segregates documents across buckets (`/recebidos`, `/processados`, `/auditoria_humana`). |
| **UI & API** | FastAPI + Streamlit / Gradio | REST endpoints for automated ingestion + intuitive dashboard for Human-in-the-Loop clinical auditors. |
| **Environment** | WSL (Ubuntu-24.04) / Python 3.12+ | Isolated Linux environment conforming to project boundaries. |

---

## 3. Data Schema & Core Contracts

### 3.1 Ingestion Payload (Input)
```json
{
  "documento_id": "DOC-CLIN-2026-8942",
  "tipo_arquivo": "PDF",
  "documento_texto": "HOSPITAL SANTA LUCIA - LAUDO DE EXAME RADIOLOGICO...",
  "arquivo_binario_b64": null,
  "canal_origem": "Pronto_Socorro"
}
```

### 3.2 Triage & Extraction Output (Target Contract)
```json
{
  "status": "processado",
  "documento_id": "DOC-CLIN-2026-8942",
  "classificacao": {
    "tipo_documento": "Laudo de Exame de Imagem",
    "especialidade": "Radiologia / Pneumologia",
    "nivel_prioridade": "Urgente",
    "score_confianca_classificacao": 0.99
  },
  "dados_extraidos": {
    "paciente": {
      "nome": "Carlos Eduardo Mendes",
      "idade": 52
    },
    "medico_solicitante": {
      "nome": "Dra. Renata Silveira",
      "crm": "145892-SP"
    },
    "exame_realizado": "Tomografia de Torax com contraste",
    "diagnostico_principal": "Tromboembolismo Pulmonar Agudo (TEP)",
    "cid_sugerido": "I26.9"
  },
  "decisao_roteamento": {
    "destino_principal": "Fila_Emergencia_Medica",
    "requer_auditoria_humana": false,
    "justificativa_roteamento": "Achado critico de alta gravidade (TEP agudo) detectado em paciente sintomatico.",
    "notificacao_gerada": {
      "canal": "Alerta_Plantao_Medico",
      "mensagem": "ALERTA URGENTE: Laudo critico de TEP Agudo para paciente Carlos Eduardo Mendes no Pronto-Socorro."
    }
  },
  "armazenamento_oci": {
    "bucket": "mediflow-documentos-clinicos",
    "caminho_objeto": "processados/urgentes/DOC-CLIN-2026-8942.json",
    "status_backup": "sucesso"
  }
}
```

---

## 4. Architectural Decision Records (ADRs)

- **ADR-001: LangGraph for Agentic Decision Graph**
  - *Context:* The pipeline requires conditional branching based on confidence score and emergency criteria.
  - *Decision:* Adopt LangGraph to model nodes (Ingestion -> Classifier -> Extractor -> Validator -> Router -> Storage).
  - *Status:* Approved.

- **ADR-002: Trilingual Documentation (EN-US / PT-BR / ES)**
  - *Context:* The project is developed for ONE G10 Brasil & LATAM, demanding inclusive Latin American & international standards.
  - *Decision:* Maintain README in EN-US, PT-BR, and ES side-by-side.
  - *Status:* Implemented.

- **ADR-003: Strict Always Free Tier Policy for OCI**
  - *Context:* Compliance with ONE social program rules.
  - *Decision:* All cloud resources must strictly utilize OCI Always Free tiers (Object Storage, Compute A1/E2.1 if deployed).
  - *Status:* Active.

- **ADR-004: Git Tracking Segregation**
  - *Context:* Workspace memory and ephemeral plan files must not clutter git history unless designated.
  - *Decision:* Add `memory.md` to `.gitignore`; keep `README.md` and `LICENSE` tracked.
  - *Status:* Implemented.

---

## 5. Execution Roadmap & Deliverables Tracker

### Milestone 1: Planning & Specifications (Current - v0.1)
- [x] Analyze `medflow.md` specifications and extract requirements.
- [x] Create persistent memory file (`memory.md`).
- [x] Author Core Specification v0.1 in `README.md` (EN-US, PT-BR, and ES).
- [x] Configure `.gitignore` to protect internal memory/plan files.
- [x] Add standard MIT License.

### Milestone 2: Core Data Models & LLM Extraction Engine
- [ ] Implement Pydantic models for Document Input, Clinical Entity Extraction, and Triage Output.
- [ ] Implement Multimodal Ingestion Module (PDF/image parser, base64 / text normalization).
- [ ] Configure Gemini / LLM prompts with few-shot clinical examples and structured output schema.
- [ ] Implement Confidence Score Calculation heuristic and CID-10 mapping.

### Milestone 3: Decision Graph & Agent Workflow
- [ ] Define LangGraph State schema.
- [ ] Implement conditional routing nodes:
  - Standard Routine Flow (Low risk, High confidence -> Pep/PEP Archive / Farmacia / Auditoria)
  - Urgency Flow (Critical findings / TEP / Infarct -> Fila Emergência / Alerta Plantão)
  - Human-in-the-Loop Fallback (Low confidence < 0.85 / Missing data -> Fila Revisão Humana)
- [ ] Unit tests for the 3 mandatory evaluation scenarios.

### Milestone 4: OCI Object Storage Integration
- [ ] Configure OCI SDK / REST integration using OCI Always Free configuration.
- [ ] Implement bucket segregation:
  - `mediflow-documentos-clinicos/recebidos/`
  - `mediflow-documentos-clinicos/processados/rotina/`
  - `mediflow-documentos-clinicos/processados/urgentes/`
  - `mediflow-documentos-clinicos/auditoria_humana/`
- [ ] Implement fallback mock storage for offline/local development.

### Milestone 5: UI & Auditor Dashboard (HitL)
- [ ] Build Streamlit / FastAPI interface for document ingestion and real-time triage visualization.
- [ ] Build Human-in-the-Loop review screen allowing one-click approval/rejection and field correction.

### Milestone 6: Final Validation, Demonstration & Submission
- [ ] End-to-end testing with sample clinical PDFs and images.
- [ ] Record demonstration videos and document test cases in `README.md`.
- [ ] Final repository readiness check for ONE G10 submission.

---

## 6. Project Updates & Changelog

### [2026-10-23] — Milestone 1: Inception & Core Spec v0.1
- **Author:** Equipo 22 / Pair Programming Assistant
- **Actions Completed:**
  - Ingested and parsed `G10-BRASIL-equipo-22-Medflow/Docs/medflow.md`.
  - Created `memory.md` to track project evolution until final delivery.
  - Formulated Core Specification v0.1.
  - Rewrote `README.md` with trilingual (EN-US, PT-BR, ES) specifications, architecture diagrams, data contracts, and roadmap.
  - Added `memory.md` to `.gitignore`.
  - Created official `LICENSE` (MIT).
- **Status:** Milestone 1 complete.

### [2026-10-23] — Milestone 2: Test Guide & Activation Sequence (`test.md`)
- **Author:** Equipo 22 / Pair Programming Assistant
- **Actions Completed:**
  - Created [`test.md`](file:///home/magno/ONE/test.md) detailing the complete WSL activation sequence, environment dependencies, Pydantic contract validation, OCI storage fallback testing, execution of the 3 Hackathon clinical test scenarios (Routine, Emergency TEP, Ambiguous HitL), FastAPI REST commands, and Streamlit HitL dashboard walkthrough.
  - Added `test.md` to [`.gitignore`](file:///home/magno/ONE/.gitignore) to keep internal testing sequences local.
- **Status:** Test catalog ready for local validation.

### [2026-10-23] — Milestone 2.1: NVIDIA NIM Integration (`meta/llama-3.2-11b-vision-instruct`)
- **Author:** Equipo 22 / Pair Programming Assistant
- **Actions Completed:**
  - Integrated NVIDIA NIM API into [`mediflow_agent.py`](file:///home/magno/ONE/mediflow_agent.py) with model `meta/llama-3.2-11b-vision-instruct`.
  - Added support for multimodal vision extraction (Base64 images and PDFs) with strict structured JSON output parsing.
  - Implemented zero-downtime SRE fallback: seamless transition to the local heuristic clinical engine if offline or without key.
  - Added telemetria status in [`app.py`](file:///home/magno/ONE/app.py) Streamlit sidebar and updated [`test.md`](file:///home/magno/ONE/test.md) with NVIDIA API testing steps.
- **Status:** NVIDIA NIM multimodal LLM engine fully integrated and verified.

### [2026-10-23] — Milestone 2.2: Continuous Improvements & Engineering Challenges Tracking
- **Author:** Equipo 22 / Pair Programming Assistant
- **Actions Completed:**
  - Created [`melhorias.md`](file:///home/magno/ONE/melhorias.md) to record all implemented enhancements (SRE fallback, NVIDIA NIM vision, cold-start handling, Pydantic compatibility, HitL panel) and backlog of planned improvements.
  - Created [`desafios.md`](file:///home/magno/ONE/desafios.md) detailing root cause analyses of cold-starts, HTTP 500s, OCI Always Free constraints, clinical ambiguity handling, and the project risk matrix.
  - Added both `melhorias.md` and `desafios.md` to [`.gitignore`](file:///home/magno/ONE/.gitignore) to maintain them strictly local.
- **Status:** Tracking documents configured.

### [2026-10-24] — Milestone 2.3: Squad Expansion (Fernando Szekut) & Schedule Rebalancing
- **Author:** Equipo 22 / Pair Programming Assistant
- **Actions Completed:**
  - Integrated Fernando Szekut ([GitHub: FSzekut](https://github.com/FSzekut) | [Portfólio](https://fernando-szekut.netlify.app/)) as the 4th member of Equipo 22 under the persona **Fernando Nexus** (Agent Integration, Frontend/UX & Workflows).
  - Maintained Carlos as **Tech Lead & SRE/DevOps**, keeping core AI architecture, LangGraph, Pydantic contracts, CI/CD, and reliability governance.
  - Rebalanced the 6-week schedule, Kanban issues (`setup_github_kanban.sh`), and the RACI matrix in [`PLANO_PROJETO_MEDIFLOW_HACKATHON.md`](file:///home/magno/ONE/PLANO_PROJETO_MEDIFLOW_HACKATHON.md).
  - Updated codebase headers and team telemetry in [`app.py`](file:///home/magno/ONE/app.py), [`mediflow_agent.py`](file:///home/magno/ONE/mediflow_agent.py), [`mediflow_schemas.py`](file:///home/magno/ONE/mediflow_schemas.py), [`oci_storage.py`](file:///home/magno/ONE/oci_storage.py), [`melhorias.md`](file:///home/magno/ONE/melhorias.md), [`desafios.md`](file:///home/magno/ONE/desafios.md) and [`test.md`](file:///home/magno/ONE/test.md).
- **Status:** Team expansion consolidated across project governance and code artifacts.

### [2026-10-24] — Milestone 2.4: Professional Profiles & Links Update
- **Author:** Equipo 22 / Pair Programming Assistant
- **Actions Completed:**
  - Added Carlos Magno's GitHub ([magnomct](https://github.com/magnomct)) and Portfolio ([carlosmagnocloudengineer.vercel.app/en](https://carlosmagnocloudengineer.vercel.app/en)) to [`PLANO_PROJETO_MEDIFLOW_HACKATHON.md`](file:///home/magno/ONE/PLANO_PROJETO_MEDIFLOW_HACKATHON.md) across Persona 1, RACI matrix and Deliverables section.
- **Status:** Documentation aligned with complete team professional profiles.

### [2026-10-24] — Milestone 3.0: Week 3 Sprint Planning (LangGraph & Notification Workflows)
- **Author:** Equipo 22 / Pair Programming Assistant
- **Actions Completed:**
  - Programmed the full operational roadmap for Week 3 (26/10 a 30/10/2026 — Dias Úteis) in [`SEMANA_3_GRAFO_WORKFLOWS_KANBAN.md`](file:///home/magno/ONE/SEMANA_3_GRAFO_WORKFLOWS_KANBAN.md).
  - Defined the 12 sprint cards distributed among the 4 team members: Carlos (LangGraph StateGraph, SRE telemetry & chaos testing), Fernando (Webhooks module & plantão médico alerts), Helder (transactional audit & dynamic OCI folders), Alessandro (FastAPI graph endpoints & pytest suite).
  - Created [`setup_kanban_semana_3.sh`](file:///home/magno/ONE/setup_kanban_semana_3.sh) for GitHub Projects automated issue provisioning.
  - Added all Week 3 management files to [`.gitignore`](file:///home/magno/ONE/.gitignore) to keep them strictly local without pushing to GitHub.
- **Status:** Sprint M3 fully scheduled, mapped, and ready for execution.

### [2026-10-27] — Milestone 3.1: Release 1.3 Implementation & Automated Test Suite
- **Author:** Carlos Magno (Tech Lead & SRE) / Pair Programming Assistant
- **Actions Completed:**
  - Created isolated local branch `release-1.3` (off of `main`, strictly local, not pushed to GitHub).
  - Created modular directory [`week3/`](file:///home/magno/ONE/week3):
    - [`week3/agent.py`](file:///home/magno/ONE/week3/agent.py): Formal LangGraph `StateGraph` implementation with typed state, conditional router edge, multimodal vision / text classification, and zero-downtime SRE fallback.
    - [`week3/notifications.py`](file:///home/magno/ONE/week3/notifications.py): Real-time `NotificationDispatcher` supporting external webhooks and mock mode for `Alerta_Plantao_Medico`.
    - [`week3/storage.py`](file:///home/magno/ONE/week3/storage.py): `OCIStorageServiceV3` with dynamic path segregation by specialty (`processados/{prioridade}/{especialidade}/...`), local SQLite transactional audit log, and Always Free compliance monitoring.
    - [`week3/api.py`](file:///home/magno/ONE/week3/api.py): FastAPI v1.3 REST API with StateGraph inspection (`/api/v1/grafo/estrutura`), triage, HitL approval, SRE telemetry, and OCI compliance endpoints.
    - [`week3/test_week3.py`](file:///home/magno/ONE/week3/test_week3.py): 8 comprehensive automated unit and integration tests (100% pass rate in 1.24s).
    - [`week3/run_tests.py`](file:///home/magno/ONE/week3/run_tests.py): Standalone CLI test runner with formatted executive report banner for Thursday's squad review.
    - [`week3/README.md`](file:///home/magno/ONE/week3/README.md): Briefing guide and architecture documentation for the team alignment meeting.
  - Updated [`.gitignore`](file:///home/magno/ONE/.gitignore) to protect SQLite databases (`*.db`, `*.sqlite`) and local caches.
- **Status:** Release 1.3 100% completed, tested, and validated locally for Thursday squad homologation.

### [2026-10-29] — Milestone 3.2: Business Days Schedule Alignment, Git Files Release & Kanban Sync
- **Author:** Carlos Magno (Tech Lead & SRE) / Pair Programming Assistant
- **Actions Completed:**
  - Standardized the entire project timeline to strictly count **business days (Segunda a Sexta-feira)**:
    - **Semana 1:** 12/10 a 16/10/2026 (Concluído)
    - **Semana 2:** 19/10 a 23/10/2026 (Concluído)
    - **Semana 3:** 26/10 a 30/10/2026 (Semana Atual — Em Homologação/Conclusão pela Squad)
    - **Semana 4:** 02/11 a 06/11/2026 (Planejado)
    - **Semana 5:** 09/11 a 13/11/2026 (Planejado)
    - **Semana 6:** 16/11 a 20/11/2026 (Planejado)
  - Updated [`.gitignore`](file:///home/magno/ONE/.gitignore) to release all core codebase (`app.py`, `mediflow_*.py`, `oci_storage.py`, `week3/`), scripts, tests, and documentation for team collaboration on Git, while strictly keeping credentials (`.env`, `*.env`), libraries (`.venv/`), local SQLite databases (`*.db`), and caches private.
  - Synchronized the Kanban backlog and GitHub Projects automation scripts across [`PLANO_PROJETO_MEDIFLOW_HACKATHON.md`](file:///home/magno/ONE/PLANO_PROJETO_MEDIFLOW_HACKATHON.md), [`SEMANA_3_GRAFO_WORKFLOWS_KANBAN.md`](file:///home/magno/ONE/SEMANA_3_GRAFO_WORKFLOWS_KANBAN.md), [`setup_github_kanban.sh`](file:///home/magno/ONE/setup_github_kanban.sh), and [`setup_kanban_semana_3.sh`](file:///home/magno/ONE/setup_kanban_semana_3.sh).
  - Regenerated the official executive PDF ([`PLANO_PROJETO_MEDIFLOW_HACKATHON.pdf`](file:///home/magno/ONE/PLANO_PROJETO_MEDIFLOW_HACKATHON.pdf)) with the corrected business-day dates and Kanban milestones.
- **Status:** Timeline, Kanban, and Git visibility fully aligned for team review.

