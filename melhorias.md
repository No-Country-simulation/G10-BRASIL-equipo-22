# 📈 MediFlow — Registro Contínuo de Melhorias e Otimizações

**Projeto:** MediFlow — Agente Autônomo para Triagem, Extração e Roteamento de Documentos Clínicos  
**Iniciativa:** Hackathon ONE G10 — Oracle Next Education & Alura  
**Squad:** Equipo 22 (Carlos Vance — Tech Lead & SRE/IA, Fernando Nexus — Frontend & Agent Workflows, Atlas Data — Helder, Marcus Builder — Alessandro)  
**Ambiente:** WSL (Ubuntu 24.04) · Python 3.12+ · OCI Always Free  
**Visibilidade:** Documento Interno de Engenharia (ignorado no Git via `.gitignore`)  

---

## 1. 🏆 Melhorias Já Implementadas

| ID | Data | Domínio | Descrição da Melhoria | Impacto / Benefício |
| :--- | :--- | :--- | :--- | :--- |
| **MEL-001** | 2026-10-23 | **Arquitetura SRE** | **Motor de Fallback Clínico Resiliente (Zero Downtime)**: implementação de pipeline híbrido onde a ausência de conectividade externa não quebra a execução. | Garante 100% de disponibilidade durante bancas de avaliação e demos gravadas. |
| **MEL-002** | 2026-10-23 | **IA Multimodal** | **Integração com NVIDIA NIM (`meta/llama-3.2-11b-vision-instruct`)**: suporte a extração multimodal de laudos e receitas em JSON estruturado com modelo de visão. | Leitura de fotos escaneadas e alta fidelidade em termos clínicos e CID-10 a custo zero. |
| **MEL-003** | 2026-10-23 | **Resiliência SRE** | **Tratamento de Cold-Start e Retentativas HTTP**: aumento do timeout para 60s e mecanismo de retry exponencial de 2s para códigos HTTP 500/502/503. | Elimina falhas de inicialização em clusters de GPU sob demanda. |
| **MEL-004** | 2026-10-23 | **Modelagem de Dados** | **Camada de Compatibilidade Pydantic v1/v2 (`_CompatBaseModel`)**: serialização segura transparente independente da versão instalada. | Elimina avisos de depreciação e incompatibilidade de pacotes. |
| **MEL-005** | 2026-10-23 | **Experiência (UX/UI)** | **Painel de Auditoria Human-in-the-Loop em Streamlit**: aba dedicada para validação humana com campo de correção de CRM e liberação em 1 clique. | Cumpre o requisito diferencial do edital ONE G10 com interface intuitiva. |
| **MEL-006** | 2026-10-23 | **Internacionalização** | **Documentação Técnica Trilíngue (README.md em EN-US, PT-BR e ES)**: especificações completas com diagramas Mermaid em 3 idiomas. | Padrão profissional global e alinhamento com a comunidade LATAM da Oracle/Alura. |
| **MEL-007** | 2026-10-23 | **Integração Cloud** | **Segregação de Prefixos OCI Always Free**: roteamento determinístico para `/recebidos`, `/processados/rotina`, `/processados/urgentes` e `/auditoria_humana`. | Auditoria completa de dados sem gerar custos de faturamento. |
| **MEL-008** | 2026-10-27 | **Workflows & Notificações** | **Despachador de Webhooks em Tempo Real (`NotificationDispatcher`)**: módulo criado por Fernando Szekut para envio de alertas críticos hospitalares com suporte a modo Mock e HTTP real resiliente. | Notificação instantânea da equipe de plantão para casos como TEP Agudo e IAM. |
| **MEL-009** | 2026-10-27 | **Orquestração de Agentes** | **Migração para LangGraph StateGraph Formal**: refatoração do fluxo clínico em grafo de estados com nós tipados, arestas condicionais e roteamento determinístico. | Robustez de estado, inspeção visual via diagrama Mermaid e conformidade estrita de tipagem. |
| **MEL-010** | 2026-10-27 | **Engenharia de Dados** | **Segregação Dinâmica de Pastas OCI por Especialidade Médica**: particionamento em `processados/{prioridade}/{especialidade}/...` com sanitização automática de slugs. | Organização escalável e busca otimizada de documentos clínicos no Object Storage. |
| **MEL-011** | 2026-10-27 | **Persistência & Auditoria** | **Histórico Transacional em SQLite Local (`triagem_audit_log`)**: persistência imediata de cada decisão, score, médico e latência SRE, com atualização transacional pós-auditoria. | Rastreabilidade clínica total para auditorias médico-legais e cálculo de SLAs. |
| **MEL-012** | 2026-10-27 | **Qualidade & SRE** | **Suite Completa de Auto-Testes Automatizados (8 testes)**: runner executivo CLI (`run_tests.py`) e cobertura de 100% dos cenários (Rotina, TEP, HitL, Webhooks, OCI, SQLite, SLA e FastAPI). | Homologação ágil e confiável para apresentação da equipe na reunião de alinhamento. |
| **MEL-013** | 2026-10-27 | **Backend & API** | **FastAPI v1.3 com Inspeção Topológica do Grafo**: novos endpoints `/api/v1/grafo/estrutura` e `/api/v1/telemetria` expondo a topologia do StateGraph e métricas SRE. | Facilita a integração com frontends modernos e sistemas hospitalareslegados. |
| **MEL-014** | 2026-10-29 | **Governança & Gestão** | **Padronização do Cronograma em Dias Úteis (Seg-Sex) & Liberação Git**: ajuste rigoroso de todas as 6 semanas para dias úteis e liberação de código para a squad mantendo `.env` e segredos blindados. | Garante colaboração ágil do time sem riscos de vazamento de credenciais na nuvem. |

---

## 2. 🚀 Backlog de Próximas Melhorias Planejadas

### 2.1 Performance & IA
- [ ] **Otimização de Prompt e Token Caching**: Reduzir o número de tokens do system prompt para diminuir a latência média da NVIDIA NIM de ~5s para $< 2\text{s}$.
- [ ] **Conversor Automático de PDF para Imagem**: Usar `pypdf` + `Pillow` para converter a primeira página de PDFs digitalizados em imagem Base64, enviando diretamente para a visão multimodal do Llama 3.2.
- [ ] **Suporte a Múltiplos Provedores de LLM**: Chave seletora rápida entre NVIDIA NIM, Google Gemini Flash e Groq Cloud via variável `AI_PROVIDER`.

### 2.2 Persistência e Dados (OCI Always Free)
- [ ] **Histórico Relacional em OCI Autonomous Database (ATP)**: Gravação de registros de auditoria em tabela relacional com colunas JSON para busca rápida por CRM e data.
- [ ] **Expurgo e Retenção Automática**: Política de retenção de 30 dias para documentos brutos em `/recebidos`, mantendo conformidade com boas práticas de governança de dados.

### 2.3 Interface e Human-in-the-Loop (Streamlit / FastAPI)
- [ ] **Visualizador de PDF/Imagem Lado a Lado no Streamlit**: Exibir a imagem do documento original ao lado do formulário de auditoria na Aba HitL.
- [ ] **Filtro de Fila por Gravidade**: Permitir que auditores priorizem a análise de documentos marcados com suspeita de urgência clínica.
- [ ] **Notificação Real-Time (Webhooks)**: Envio de alertas de casos urgentes (TEP / IAM) para canais externos como Slack ou Discord.

### 2.4 Diferenciais Competitivos (Edital ONE G10)
- [ ] **Editor de Regras de Triagem sem Código**: Interface onde o diretor clínico pode cadastrar novas palavras-chave de urgência e seus destinos sem alterar o código Python.

