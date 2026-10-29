# 🏥 Planejamento Operacional & Kanban da Semana 3 — MediFlow (Equipo 22)

**Projeto:** MediFlow — Agente Autônomo para Triagem, Extração e Roteamento de Documentos Clínicos  
**Iniciativa:** Hackathon ONE G10 — Oracle Next Education & Alura  
**Milestone:** **M3 — Grafo de Decisão Condicional (LangGraph), Orquestração e Workflows de Notificação**  
**Período da Sprint (Dias Úteis):** 26/10/2026 a 30/10/2026 (Segunda a Sexta · Semana 3 de 6)  
**Squad:**  
- **Carlos Magno (Tech Lead):** Líder SRE/DevOps, Arquitetura IA & Python Core ([GitHub](https://github.com/magnomct) · [Portfólio](https://carlosmagnocloudengineer.vercel.app/en))  
- **Fernando Szekut (Fernando Nexus):** Engenheiro de Integração de Agentes, Frontend/UX & Workflows ([GitHub](https://github.com/FSzekut) · [Portfólio](https://fernando-szekut.netlify.app/))  
- **Helder (Atlas Data):** Especialista em Banco de Dados & Persistência OCI Always Free  
- **Alessandro (Marcus Builder):** Desenvolvedor Backend FastAPI, Módulo HitL & QA  
**Visibilidade:** Documento Oficial de Gestão e Engenharia da Squad (Liberado para o Git)  

---

## 1. 🎯 Objetivo Central da Semana 3

Consolidar o motor do MediFlow em um **Grafo de Decisão Condicional compilado formalmente no LangGraph (`StateGraph`)**, adicionando **automação de workflows de notificação em tempo real (Webhooks para plantão médico)**, persistência estruturada com auditoria transacional na **OCI Always Free**, e novos endpoints na API **FastAPI**.

### 🌟 Entregáveis de Destaque da Sprint:
1. **Grafo LangGraph Compilado (`mediflow_agent.py`)**: Migração da orquestração sequencial para a máquina de estados formal do LangGraph com nós assíncronos e arestas condicionais.
2. **Módulo de Notificações em Tempo Real (`mediflow_notifications.py`)**: Dispatcher de Webhooks para alertas hospitalares (Cenário 2 — TEP Agudo / IAM).
3. **Auditoria Transacional OCI Always Free**: Histórico append-only de decisões clínicas garantindo custo zero.
4. **Suíte de Testes Automatizados da Semana 3 (`tests/test_semana_3.py`)**: Validação de 100% dos fluxos do grafo com pytest.

---

## 2. 📋 Backlog e Divisão de Tarefas por Integrante

### 🛠️ Carlos Magno — Tech Lead, Líder SRE/DevOps, Arquitetura de IA & Python Core
> **Foco:** Orquestração do StateGraph no LangGraph, travas de segurança clínica e confiabilidade SRE.

- **[CARD-01] Refatoração do `mediflow_agent.py` com LangGraph `StateGraph` Formal:**
  - Definir o `TypedDict` ou classe de estado do grafo (`MediFlowAgentState`).
  - Mapear nós determinísticos: `ingestor_node` $\rightarrow$ `classifier_extractor_node` $\rightarrow$ `validator_sre_node` $\rightarrow$ `router_edge` $\rightarrow$ `[emergency_node | routine_node | hitl_node]` $\rightarrow$ `oci_persistence_node`.
  - Compilar o grafo com `.compile()` suportando execução síncrona e assíncrona.
- **[CARD-02] Telemetria de Observabilidade SRE no Estado do Grafo:**
  - Registrar métricas no payload: latência por nó (ms), provedor LLM ativo (`NVIDIA NIM Llama 3.2 11B` vs `Fallback Heurístico SRE`) e contagem de retentativas.
  - Implementar verificação de SLA: alertar se o tempo total de processamento exceder $5\text{s}$.
- **[CARD-03] Teste de Resiliência de Caos (Chaos / Network Degradation):**
  - Simular queda de conectividade externa e garantir que o grafo finalize com sucesso no nó de fallback sem exceções não tratadas.

---

### 🌐 Fernando Szekut — Engenheiro de Integração de Agentes, Frontend/UX & Workflows
> **Foco:** Automação de alertas em tempo real (Webhooks), visualização de notificações e pipeline multimodal.

- **[CARD-04] Desenvolvimento do Módulo de Notificações (`mediflow_notifications.py`):**
  - Implementar o despachador de Webhooks HTTP POST para envio instantâneo do payload de emergência quando `nivel_prioridade == 'Urgente'`.
  - Suporte a templates formatados para múltiplos canais: Slack, Discord e endpoint REST genérico hospitalar.
- **[CARD-05] Integração do Webhook no Nó de Emergência (`EmergencyRouteNode`):**
  - Conectar o disparo assíncrono do webhook no momento em que o laudo de TEP Agudo (Cenário 2) for roteado para a `Fila_Emergencia_Medica`.
  - Gerar payload de notificação com: Paciente, Diagnóstico, CRM do Solicitante e Link Seguro para visualização.
- **[CARD-06] Indicador de Alerta em Tempo Real no Streamlit:**
  - Criar componente visual na Aba de Triagem (`app.py`) simulando o pop-up do alerta recebido pelo médico de plantão com som/badge pulsante.

---

### 🗄️ Helder — Especialista em Banco de Dados, Persistência OCI Always Free & Modelagem
> **Foco:** Segregação dinâmica no Object Storage, histórico auditável de prontuário e compliance de custos.

- **[CARD-07] Persistência Auditável Transacional (SQLite Local + OCI Object Storage):**
  - Implementar tabela de log de triagens: `id`, `documento_id`, `status`, `tipo_documento`, `prioridade`, `score`, `caminho_oci`, `criado_em`.
  - Garantir integridade referencial para rastrear alterações realizadas por auditores humanos no HitL.
- **[CARD-08] Segregação Dinâmica por Especialidade no Bucket OCI:**
  - Refinar o `OCIStorageService` para organizar subpastas por especialidade clínica:
    - `processados/rotina/{especialidade}/{doc_id}.json`
    - `processados/urgentes/{especialidade}/{doc_id}.json`
    - `auditoria_humana/{especialidade}/{doc_id}.json`
- **[CARD-09] Script de Auditoria de Custos e Cotas OCI (Always Free):**
  - Implementar rotina de monitoramento de armazenamento garantindo respeito ao limite gratuito de 10 GB e 50.000 requisições/mês.

---

### 🚀 Alessandro — Desenvolvedor Backend FastAPI, Módulo HitL & Scrum/QA
> **Foco:** Endpoints REST FastAPI para o grafo, automação do Kanban no GitHub e suíte de testes pytest.

- **[CARD-10] Expansão da API FastAPI (`app.py`) para Inspeção do Grafo:**
  - Endpoint `GET /api/v1/grafo/estrutura`: retorna o diagrama/nós do grafo em formato JSON e Mermaid.
  - Endpoint `GET /api/v1/telemetria`: expõe métricas de latência e taxa de acerto da LLM NVIDIA.
- **[CARD-11] Construção da Suíte de Testes Automatizados da Semana 3 (`tests/test_semana_3.py`):**
  - Teste 1: Validação do StateGraph compilado para os 3 cenários oficiais (Rotina, TEP, HitL).
  - Teste 2: Mock de envio de Webhook de emergência garantindo resposta HTTP 200.
  - Teste 3: Teste de concorrência com 10 requisições simultâneas via `httpx.AsyncClient`.
- **[CARD-12] Operacionalização do Kanban GitHub Projects (`setup_kanban_semana_3.sh`):**
  - Executar o script de criação das 12 issues no GitHub Projects da equipe e organizar as colunas do sprint.

---

## 3. 📊 Matriz do Quadro Kanban da Semana 3

```mermaid
kanban
  Todo
    [CARD-01] Refatoração StateGraph LangGraph (Carlos)
    [CARD-04] Módulo de Notificações Webhooks (Fernando)
    [CARD-07] Histórico Auditável Transacional (Helder)
    [CARD-10] Endpoints de Inspeção do Grafo FastAPI (Alessandro)
  InProgress
    [CARD-02] Telemetria SRE de Latência por Nó (Carlos)
    [CARD-05] Integração Webhook Nó Emergência (Fernando)
    [CARD-08] Segregação Dinâmica por Especialidade (Helder)
    [CARD-11] Suíte de Testes pytest Semana 3 (Alessandro)
  Review_SRE
    [CARD-03] Teste de Caos e Degradação SRE (Carlos)
    [CARD-06] Componente Visual de Alerta no Streamlit (Fernando)
    [CARD-09] Auditoria de Custos Zero OCI (Helder)
  Done
    [CARD-12] Setup de Issues no GitHub Projects (Alessandro)
```

---

## 4. 📅 Calendário de Entregas da Semana 3 (Segunda a Sexta — Dias Úteis)

| Dia | Data | Marco do Dia | Responsáveis | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Segunda** | 26/10/2026 | Setup do Kanban GitHub Projects, modelagem do `StateGraph` LangGraph e contratos de estado tipado (`MediFlowAgentState`). | **Alessandro** (Kanban) e **Carlos** (Arquitetura & IA) | ✅ **Concluído** |
| **Terça** | 27/10/2026 | Implementação dos nós do LangGraph (`week3/agent.py`) e despachador de Webhooks (`week3/notifications.py`). | **Carlos** (LangGraph Core) e **Fernando** (Workflows) | ✅ **Concluído** |
| **Quarta** | 28/10/2026 | Segregação dinâmica por especialidade no OCI Always Free e log transacional SQLite (`week3/storage.py`). | **Helder** (Dados & OCI) e **Carlos** (SRE) | ✅ **Concluído** |
| **Quinta** | 29/10/2026 | API REST FastAPI v1.3 com endpoints de inspeção e HitL (`week3/api.py`), suite de 8 auto-testes (`week3/test_week3.py`) e alinhamento com a squad. | **Alessandro** (Backend), **Carlos** (SRE) e **Fernando** (UX) | 🔄 **Em Andamento (Hoje)** |
| **Sexta** | 30/10/2026 | Validação executiva de auto-testes (`week3/run_tests.py`), homologação final com a squad e liberação para sincronização no Git. | **Toda a Equipe (Equipo 22)** | ⏳ **Amanhã** |

---

## 5. ✅ Critérios de Aceite da Sprint (Definition of Done - DoD)

- [x] O grafo de decisão deve ser formalmente executável através do `StateGraph` do LangGraph (`week3/agent.py`).
- [x] O Cenário 2 (TEP Agudo) deve acionar automaticamente a notificação Webhook para o plantão médico em $< 1\text{s}$ após a classificação (`week3/notifications.py`).
- [x] O Cenário 3 (HitL) deve continuar sendo retido na fila com score $< 0.85$ e persistido em `auditoria_humana/`.
- [x] 100% dos 8 testes unitários e de integração em `week3/test_week3.py` devem passar sem falhas.
- [x] Interface gráfica web disponível na porta 8000 (`week3/api.py`) e painel Streamlit (`week3/app.py`).
- [x] Arquivos da sprint homologados e liberados no `.gitignore` para compartilhamento seguro com a squad no Git.
- [x] Cumprimento absoluto do teto orçamentário gratuito (R$ 0,00) na Oracle Cloud Infrastructure.

