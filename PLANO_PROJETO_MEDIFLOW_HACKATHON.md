# 🏥 Plano Executivo, Personas de IA, Kanban, Cronograma e Entregáveis — MediFlow (Equipo 22)

**Projeto:** MediFlow — Agente Autônomo para Triagem, Extração e Roteamento de Documentos Clínicos  
**Iniciativa:** Hackathon ONE G10 — Oracle Next Education & Alura  
**Squad / Equipe:** Equipo 22 — Carlos (Tech Lead & SRE), Fernando Szekut (Frontend & Agent Integration), Helder (Banco de Dados & OCI) e Alessandro (Backend & HitL QA)  
**Status Atual:** Semana 3 de 6 (Milestone 3: Grafo Condicional LangGraph, Workflows de Notificação & OCI Always Free)  
**Ambiente Base:** WSL (Ubuntu 24.04) · Python 3.12+ · LangGraph · Pydantic · NVIDIA NIM / Gemini · OCI Object Storage & Database (Always Free)  

---

## 1. Arquitetura das 4 Personas Técnicas Especialistas do Equipo 22

Alinhando as personas aos talentos complementares do time de 4 pessoas (**Carlos**, **Fernando Szekut**, **Helder** e **Alessandro**), estruturamos **4 Personas Técnicas Especialistas**:

| Persona Especialista | Perfil & Papéis Integrados | Integrante Responsável (Líder) | Foco Prático no MediFlow (`medflow.md` & `README.md`) |
| :--- | :--- | :--- | :--- |
| **Persona 1: Arquiteto Carlos Vance** | **Tech Lead, Líder SRE/DevOps, Arquitetura de IA & Python Core** | **Carlos (Você)**<br>([GitHub](https://github.com/magnomct) · [Portfólio](https://carlosmagnocloudengineer.vercel.app/en)) | Liderança técnica e governança da solução, arquitetura do grafo de decisão condicional em **LangGraph**, modelos **Pydantic**, integração do motor multimodal (**NVIDIA NIM Llama 3.2 11B / Gemini**), cálculo de confiança ($\ge 0.85$), esteira de CI/CD (GitHub Actions), observabilidade SRE, SLAs e resiliência com fallback local de Zero Downtime. |
| **Persona 2: Fernando Nexus** | **Engenheiro de Integração de Agentes, Frontend/UX & Automação de Workflows** | **Fernando Szekut**<br>([GitHub](https://github.com/FSzekut) · [Portfólio](https://fernando-szekut.netlify.app/)) | Aprimoramento da experiência visual e usabilidade do painel (**Streamlit / Web UX**), suporte à ingestão multimodal de imagens/PDFs clínicos, automação de fluxos e webhooks para alertas em tempo real (Notificações de Plantão Médico TEP/IAM) e visualizador de documentos clínicos. |
| **Persona 3: Atlas Data** | **Especialista em Banco de Dados, Persistência OCI & Modelagem Relacional/NoSQL** | **Helder** | Estruturação e modelagem dos schemas de dados clínicos, segregação de buckets no **OCI Object Storage Always Free** (`/recebidos`, `/processados/rotina`, `/processados/urgentes`, `/auditoria_humana`), integração com **Autonomous Database (ATP Always Free)** ou schema relacional/documental para histórico clínico auditável. |
| **Persona 4: Marcus Builder** | **Desenvolvedor de Aplicação Backend (FastAPI), Módulo Human-in-the-Loop & Scrum/QA** | **Alessandro** | Construção das rotas REST da API oficial (**FastAPI**), implementação e testes da fila de Auditoria Humana (*Human-in-the-Loop*), manipulação de chamadas OCI SDK guiadas pela arquitetura de Carlos e Helder, organização do **Kanban no GitHub Projects** e produção do Vídeo Demo no YouTube. |

---

### 1.1 Detalhamento e System Prompts das 4 Personas

#### 🛠️ Persona 1 — Arquiteto Carlos Vance (Tech Lead, Líder SRE/DevOps, Arquitetura de IA & Python)
- **Integrante:** Carlos Magno ([GitHub: magnomct](https://github.com/magnomct) · [Portfólio: Cloud Engineer](https://carlosmagnocloudengineer.vercel.app/en))
- **Perfil Técnico:** Arquiteto de Soluções com tripla especialidade: **Liderança Técnica (Tech Lead)**, **Engenharia de Confiabilidade e Nuvem (SRE/DevOps/Cloud Engineer)** e **Arquitetura de Inteligência Artificial / Agentes com Python 3.12+**.
- **Missão no MediFlow:** Desenhar e sustentar a espinha dorsal técnica do sistema: garantir que o pipeline de agentes em LangGraph seja determinístico, ultrarrápido (latência $< 5\text{s}$), seguro contra alucinações clínicas e tolerante a falhas (resiliência operacional total de Zero Downtime com fallback SRE).
- **Responsabilidades Diretas:**
  - Liderança técnica e governança da arquitetura do repositório.
  - Desenvolver e evoluir o motor do agente em `mediflow_agent.py` (LangGraph `StateGraph`) com nós condicionais (`IngestorNode`, `ClassifierExtractorNode`, `ValidatorSRECheckNode`, `ConditionalRouterEdge`, `OCIPersistenceNode`).
  - Estabelecer a heurística de **Score de Confiança** e as travas de segurança clínica: corte em $< 0.85$ para desvio compulsório à `Fila_Revisao_Humana`.
  - Configurar a esteira de CI/CD (GitHub Actions), suíte de testes automatizados (`pytest`), linting, métricas de latência SRE e políticas de *graceful degradation*.
- **System Prompt da Persona:**
  > *"Você é o Arquiteto Carlos Vance, Tech Lead e Líder de SRE/DevOps, Arquitetura de IA e Python do projeto MediFlow (Equipo 22 - Hackathon ONE G10). Sua prioridade é assegurar a excelência técnica da solução, pipelines robustos em LangGraph e Pydantic, SLAs rigorosos de latência, observabilidade, resiliência contra falhas de terceiros e zero falso-negativo em emergências médicas (como TEP Agudo)."*

---

#### 🌐 Persona 2 — Fernando Nexus (Engenheiro de Integração de Agentes, Frontend/UX & Automação de Workflows)
- **Perfil Técnico:** Desenvolvedor focado em ecossistemas modernos de agentes autônomos, arquiteturas de conhecimento (*second brain*), experiência de usuário (UX/UI frontend) e integrações web baseadas em APIs e webhooks.
- **Missão no MediFlow:** Transformar as capacidades do agente em uma experiência clínica fluida, intuitiva e conectada, assegurando que médicos, auditores e gestores interajam perfeitamente com os documentos e que alertas de emergência cheguem instantaneamente aos canais hospitalares.
- **Responsabilidades Diretas:**
  - Refinar o frontend no Streamlit (`app.py`), implementando visualização lado a lado de laudos/receitas e dados extraídos pela IA.
  - Otimizar o pipeline multimodal de documentos clínicos (processamento de imagens em alta resolução e visualização de PDFs escaneados via Pillow/pypdf).
  - Implementar integrações de notificações e webhooks para alertas em tempo real (`Alerta_Plantao_Medico`), conectando os resultados do agente com canais de comunicação hospitalar.
  - Estruturar a base de conhecimento de apoio do agente (prompts, taxonomias de especialidades e mapeamento de terminologia médica).
- **System Prompt da Persona:**
  > *"Você é Fernando Nexus, Engenheiro de Integração de Agentes, Frontend/UX e Automação de Workflows do MediFlow (Equipo 22). Sua prioridade é projetar interfaces clínicas claras, interativas e humanizadas, enriquecer o pipeline multimodal de visão e garantir que cada decisão do agente e alerta crítico de emergência chegue com máxima agilidade e elegância visual aos profissionais de saúde."*

---

#### 🗄️ Persona 3 — Atlas Data (Especialista em Banco de Dados, Persistência OCI & Dados Clínicos)
- **Perfil Técnico:** Administrador e Engenheiro de Dados focado em bancos relacionais (Oracle Database / PostgreSQL), NoSQL/JSON Collections e Object Storage na nuvem **Oracle Cloud Infrastructure (OCI Always Free)**.
- **Missão no MediFlow:** Garantir a integridade, modelagem relacional/JSON, rastreabilidade e persistência imutável de todos os documentos clínicos, laudos e decisões de triagem nos serviços de armazenamento da OCI.
- **Responsabilidades Diretas:**
  - Desenvolver e manter o módulo `oci_storage.py`, gerenciando o bucket `mediflow-documentos-clinicos` com segregação estrita por prefixos (`recebidos/`, `processados/rotina/`, `processados/urgentes/`, `auditoria_humana/`).
  - Modelar o esquema relacional ou JSON Collection no **OCI Autonomous Transaction Processing (ATP)** ou SQLite local para histórico completo de auditoria clínica e prontuário.
  - Assegurar conformidade com a camada **OCI Always Free (ADR-003)**, garantindo custo zero e retenção segura de dados em conformidade com as diretrizes do programa ONE.
- **System Prompt da Persona:**
  > *"Você é Atlas Data, Especialista em Banco de Dados e Persistência OCI do MediFlow (Equipo 22). Sua prioridade é estruturar a modelagem dos dados clínicos em JSON estruturado e tabelas relacionais, organizar a segregação de objetos no OCI Object Storage Always Free e garantir que cada laudo, receita e decisão do agente seja perfeitamente rastreável e auditável."*

---

#### 🚀 Persona 4 — Marcus Builder (Desenvolvedor Backend FastAPI, Módulo HitL & QA)
- **Perfil Técnico:** Desenvolvedor de Software focado em APIs REST assíncronas em Python, integração de regras de negócio e controle de qualidade de ponta a ponta.
- **Missão no MediFlow:** Construir a camada de serviços REST da aplicação, operacionalizar o fluxo de **Auditoria Humana (Human-in-the-Loop)**, executar a homologação dos 3 cenários clínicos e conduzir a produção dos entregáveis e vídeo demo do Hackathon.
- **Responsabilidades Diretas:**
  - Manter e expandir os endpoints REST oficiais do **FastAPI** (`/api/v1/triagem`, `/api/v1/auditoria`, `/api/v1/auditoria/{id}/aprovar`).
  - Estruturar a lógica do painel de Human-in-the-Loop em conjunto com Fernando, garantindo aprovação e correção de CRM em 1 clique.
  - Organizar o quadro **Kanban no GitHub Projects** usando `setup_github_kanban.sh`, gerenciar os cards de sprint e gravar o **Vídeo Demo no YouTube** demonstrando os 3 cenários obrigatórios e o bucket da OCI.
- **System Prompt da Persona:**
  > *"Você é Marcus Builder, Desenvolvedor Backend e QA do MediFlow (Equipo 22). Seu objetivo é assegurar endpoints REST rápidos e padronizados, colaborar com Fernando no fluxo de Human-in-the-Loop e garantir que todos os cenários obrigatórios (Rotina, TEP e HitL) sejam testados e demonstrados com clareza impecável."*

---

## 2. Matriz de Responsabilidades (RACI) da Equipe

| Integrante | Persona | Perfil Principal | Entregas Técnicas no Repositório (`equipo-22`) |
| :--- | :--- | :--- | :--- |
| **Carlos (Você)**<br>([GitHub](https://github.com/magnomct) · [Portfólio](https://carlosmagnocloudengineer.vercel.app/en)) | **Arquiteto Carlos Vance** | **Tech Lead, SRE/DevOps, Arquitetura IA & Python Core** | 1. Arquitetura do agente em `mediflow_agent.py` com **LangGraph**, **Pydantic** e **NVIDIA NIM**.<br>2. Pipeline CI/CD no GitHub Actions (`.github/workflows/ci.yml`), testes `pytest` e métricas SRE.<br>3. Governança de arquitetura, documentação trilíngue (`README.md`), `memory.md`, `melhorias.md` e `desafios.md`. |
| **Fernando Szekut** | **Fernando Nexus** | **Integração de Agentes, Frontend/UX & Automação de Workflows** | 1. Design da experiência interativa do painel **Streamlit** (visualização lado a lado de laudos e dados extraídos).<br>2. Integração de Webhooks/Notificações de Alertas de Emergência Médica em tempo real.<br>3. Otimização do pipeline multimodal de documentos (visão computacional para receitas/laudos escaneados). |
| **Helder** | **Atlas Data** | **Banco de Dados, Persistência OCI & Modelagem de Dados** | 1. Implementação e testes de `oci_storage.py` com o OCI Python SDK e fallback resiliente Always Free.<br>2. Provisionamento e segregação do bucket `mediflow-documentos-clinicos` na **OCI Always Free**.<br>3. Modelagem de dados para prontuário eletrônico e conformidade de custos zero. |
| **Alessandro** | **Marcus Builder** | **Backend FastAPI, Módulo HitL & Scrum/QA** | 1. Endpoints REST da API em `app.py` (`/api/v1/triagem`, `/api/v1/auditoria`, aprovação HitL).<br>2. Manutenção do quadro **Kanban no GitHub Projects** (`setup_github_kanban.sh`).<br>3. Homologação dos 3 cenários clínicos de teste e gravação do **Vídeo Demo no YouTube**. |

---

## 3. Cronograma do Projeto — 6 Semanas (Dias Úteis: Segunda a Sexta)

| Semana | Período (Dias Úteis) | Milestone | Foco Principal | Responsáveis e Entregáveis | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Semana 1** | **12/10 a 16/10/2026** | **M1: Concepção & Core Spec** | Análise de `medflow.md`, ADRs e documentação base. | • **Carlos:** Core Spec v0.1, ADRs e `README.md` trilíngue.<br>• **Helder:** Setup OCI Always Free e WSL.<br>• **Alessandro & Fernando:** Estrutura Git, `LICENSE` e `memory.md`. | ✅ **Concluído** |
| **Semana 2** | **19/10 a 23/10/2026** | **M2: Modelagem de Dados & Motor LLM** | Schemas Pydantic, motor multimodal NVIDIA NIM / Gemini e OCI Storage. | • **Carlos:** `mediflow_schemas.py`, agente com NVIDIA NIM e fallback SRE.<br>• **Fernando:** Ingestão multimodal de imagens/PDFs e protótipo de UX.<br>• **Helder:** Bucket OCI `mediflow-documentos-clinicos` e `oci_storage.py`.<br>• **Alessandro:** Setup do Kanban (`setup_github_kanban.sh`) e suíte de testes. | ✅ **Concluído** |
| **Semana 3** | **26/10 a 30/10/2026** | **M3: Grafo Condicional & Workflows** | Nós do StateGraph, rotas de Emergência, Rotina, HitL e Webhooks. | • **Carlos:** Grafo LangGraph formal (`week3/agent.py`) e travas SRE.<br>• **Fernando:** Webhooks para alertas de plantão de emergência (`week3/notifications.py`).<br>• **Helder:** Persistência OCI Always Free e SQLite transacional (`week3/storage.py`).<br>• **Alessandro:** API REST FastAPI (`week3/api.py`), auto-testes (`week3/test_week3.py`) e QA. | 🔄 **Semana Atual (Em Conclusão/Homologação)** |
| **Semana 4** | **02/11 a 06/11/2026** | **M4: Banco de Dados OCI & CI/CD** | Segregação de dados OCI, histórico de prontuário, CI/CD e telemetria. | • **Helder:** Validação de uploads OCI remotos e persistência relacional.<br>• **Carlos:** GitHub Actions CI, métricas de latência SRE e retentativas.<br>• **Fernando & Alessandro:** Otimização da renderização de dados clínicos na interface. | ⏳ Planejado |
| **Semana 5** | **09/11 a 13/11/2026** | **M5: Interface Streamlit & HitL** | Dashboard para auditor clínico com visualização lado a lado e deploy OCI. | • **Fernando & Alessandro:** Interface Streamlit (`app.py` / `week3/app.py`) com aprovação HitL em 1 clique e visualizador.<br>• **Carlos:** Conexão agente-interface e testes de carga/resiliência.<br>• **Helder:** Deploy opcional em VM OCI Compute Always Free. | ⏳ Planejado |
| **Semana 6** | **16/11 a 20/11/2026** | **M6: Demonstração & Submissão ONE** | Vídeo Demo no YouTube, validação final e entrega. | • **Alessandro & Fernando:** Gravação, edição e publicação do Vídeo Demo no YouTube.<br>• **Carlos:** Revisão final de conformidade técnica, código e documentação.<br>• **Helder:** Auditoria final de custos zero na OCI e estabilidade. | ⏳ Planejado |

---

## 4. Modelo Kanban para o GitHub Projects (Sprints por Dias Úteis)

### 4.1 Estrutura de Milestones & Sprints (Segunda a Sexta):
- **Sprint M1 (12/10 a 16/10/2026):** `M1: Concepção, Core Spec v0.1 & ADRs` — ✅ **Concluído**
- **Sprint M2 (19/10 a 23/10/2026):** `M2: Schemas Pydantic, Motor NVIDIA NIM & OCI Storage` — ✅ **Concluído**
- **Sprint M3 (26/10 a 30/10/2026):** `M3: Grafo LangGraph StateGraph, Webhooks & SQLite` — 🔄 **Semana Atual (Homologação)**
- **Sprint M4 (02/11 a 06/11/2026):** `M4: Persistência Remota OCI, Prontuário & CI/CD Actions` — ⏳ Planejado
- **Sprint M5 (09/11 a 13/11/2026):** `M5: Painel Visual Streamlit & Fila HitL em 1 Clique` — ⏳ Planejado
- **Sprint M6 (16/11 a 20/11/2026):** `M6: Gravação Demo YouTube, Auditoria OCI e Submissão ONE` — ⏳ Planejado

### 4.2 Labels Oficiais de Gestão:
- **Labels das 4 Personas:**
  - `persona:carlos-sre-ia` (Azul `#0052CC`) — Carlos (Tech Lead, SRE/DevOps, Arquitetura IA & Python)
  - `persona:fernando-nexus` (Teal `#008080`) — Fernando Szekut (Integração de Agentes, Frontend/UX & Workflows)
  - `persona:helder-data-oci` (Vermelho `#D93F0B`) — Helder (Banco de Dados, Persistência OCI Always Free)
  - `persona:alessandro-app` (Roxo `#5319E7`) — Alessandro (Desenvolvedor Backend FastAPI, HitL & QA)
- **Labels de Prioridade:**
  - `priority:critical-mvp` (Amarelo `#FBCA04`) — Requisitos obrigatórios do edital ONE G10
  - `priority:differential` (Verde `#0E8A16`) — Recursos de destaque (Painel Streamlit HitL, Deploy OCI Compute, Webhooks)
- **Labels de Sprint por Dias Úteis:**
  - `sprint:semana-1` (12/10 a 16/10) · `sprint:semana-2` (19/10 a 23/10) · `sprint:semana-3` (26/10 a 30/10)
  - `sprint:semana-4` (02/11 a 06/11) · `sprint:semana-5` (09/11 a 13/11) · `sprint:semana-6` (16/11 a 20/11)

### 4.3 Visão do Quadro Kanban Atual:
```mermaid
kanban
  Concluido_M1_e_M2
    [M1] Core Spec v0.1 e ADRs (Carlos)
    [M1] Setup OCI Always Free (Helder)
    [M2] Schemas Pydantic v2 (Carlos)
    [M2] Motor NVIDIA NIM Llama 3.2 (Carlos)
    [M2] Ingestao Multimodal e UX (Fernando)
    [M2] OCI Storage Service (Helder)
  Em_Homologacao_Semana_3
    [M3] LangGraph StateGraph formal (Carlos)
    [M3] Webhook Dispatcher Plantao (Fernando)
    [M3] Segregacao OCI por Especialidade (Helder)
    [M3] SQLite Audit Transacional (Helder)
    [M3] API FastAPI v1.3 e HitL (Alessandro)
    [M3] Suite 8 Auto-Testes (Alessandro)
  Planejado_Semanas_4_a_6
    [M4] GitHub Actions CI/CD Pipeline
    [M4] Persistencia Relacional Prontuario
    [M5] Interface Streamlit Completa
    [M6] Gravacao Video Demo YouTube
```

---

## 5. Entregáveis Oficiais do Hackathon ONE G10 (Tarefas 1 a 4)

### 📄 TAREFA 1: Documentação do Projeto (Formato Markdown)
O **MediFlow** é um agente autônomo e inteligente para triagem, extração de entidades e roteamento condicional de documentos clínicos heterogêneos (laudos, receitas e guias TISS), desenvolvido pelo **Equipo 22** com **LangGraph**, **NVIDIA NIM (Llama 3.2 11B Vision)** / **Google Gemini**, **Pydantic** e persistência segregada no **Oracle Cloud Infrastructure (OCI) Object Storage (Camada Always Free)**.

- **Equipe (4 Integrantes):**
  - **Carlos:** Tech Lead, Líder SRE/DevOps, Arquitetura IA & Python Core ([GitHub](https://github.com/magnomct) · [Portfólio](https://carlosmagnocloudengineer.vercel.app/en))
  - **Fernando Szekut:** Engenheiro de Integração de Agentes, Frontend/UX & Automação de Workflows ([GitHub](https://github.com/FSzekut) · [Portfólio](https://fernando-szekut.netlify.app/))
  - **Helder:** Especialista em Banco de Dados & Persistência OCI Always Free
  - **Alessandro:** Desenvolvedor Backend FastAPI, Módulo HitL & QA
- **Diferenciais:** Grafo de decisão com 3 rotas (Emergência Médica para TEP Agudo — CID `I26.9`, Fluxo Padrão Aprovado para Farmácia/PEP, e Revisão Humana quando score $< 0.85$); persistência segregada em buckets Always Free da OCI; e painel visual em Streamlit com aprovação em 1 clique para auditores clínicos.

### 🎬 TAREFA 2: Vídeo Demo do Projeto (Link do YouTube)
- 🔗 **URL de Submissão:** `https://www.youtube.com/watch?v=MEDIFLOW_EQUIPO22_DEMO` *(Substituir pelo link final do upload da Semana 6)*
- **Roteiro de 3 Minutos:**
  1. Apresentação da equipe e do problema hospitalar de triagem manual (Alessandro).
  2. Demonstração do motor de agentes LangGraph com IA da NVIDIA nos Cenários de Rotina e Urgência TEP com alertas SRE (Carlos).
  3. Demonstração do visualizador multimodal de documentos e notificações em tempo real (Fernando).
  4. Demonstração da fila de Human-in-the-Loop no Streamlit e aprovação de CRM em 1 clique (Alessandro & Fernando).
  5. Exibição do bucket OCI Always Free com segregação de objetos e custo zero garantido (Helder).

### 🛠️ TAREFA 3: Ferramentas da Equipe
- **Linguagem & Frameworks:** Python 3.12+, LangGraph, Pydantic v2, FastAPI e Streamlit.
- **Modelos de IA:** NVIDIA NIM (`meta/llama-3.2-11b-vision-instruct`), Google Gemini API (`gemini-2.0-flash`).
- **Cloud & Dados:** OCI Object Storage Always Free, OCI Autonomous Database / JSON Storage, OCI Python SDK (`oci`), OCI Compute Instance Always Free.
- **DevOps, SRE, Frontend & QA:** WSL2 Ubuntu 24.04, Git, GitHub Projects, GitHub Actions CI, Pytest, Webhooks e Netlify.

### 🔗 TAREFA 4: Links do Projeto
- **Repositório GitHub:** `https://github.com/ONE-G10-Brasil/G10-BRASIL-equipo-22-Medflow`
- **Documentação Trilíngue (`README.md`):** `https://github.com/ONE-G10-Brasil/G10-BRASIL-equipo-22-Medflow/blob/main/README.md`
- **Kanban do Projeto:** `https://github.com/ONE-G10-Brasil/G10-BRASIL-equipo-22-Medflow/projects`
- **Vídeo Demo no YouTube:** `https://www.youtube.com/watch?v=MEDIFLOW_EQUIPO22_DEMO`
- **Bucket OCI Object Storage:** `oci://mediflow-documentos-clinicos@<tenancy-namespace>`
