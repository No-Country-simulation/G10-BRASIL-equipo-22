# 🧗 MediFlow — Registro Contínuo de Desafios Técnicos e Soluções

**Projeto:** MediFlow — Agente Autônomo para Triagem, Extração e Roteamento de Documentos Clínicos  
**Iniciativa:** Hackathon ONE G10 — Oracle Next Education & Alura  
**Squad:** Equipo 22 (Carlos Vance — Tech Lead & SRE/IA, Fernando Nexus — Frontend & Agent Workflows, Atlas Data — Helder, Marcus Builder — Alessandro)  
**Ambiente:** WSL (Ubuntu 24.04) · Python 3.12+ · OCI Always Free  
**Visibilidade:** Documento Interno de Engenharia (ignorado no Git via `.gitignore`)  

---

## 1. 🔍 Registro de Desafios Enfrentados e Superados

### Desafio 1: Cold Start e Latência na Nuvem Gratuita da NVIDIA NIM
- **Cenário:** Durante a execução do primeiro caso de teste (Cenário 1 — Rotina), a requisição excedeu o timeout com erro `The read operation timed out`.
- **Causa Raiz:** Como o endpoint gratuito de desenvolvedores da NVIDIA NIM (`build.nvidia.com`) aloca nós de inferência sob demanda, a primeira chamada sofre do efeito de *Cold Start* (alocação da GPU e inicialização do contêiner do Llama 3.2 11B Vision), levando de 35 a 45 segundos.
- **Impacto:** O teste poderia falhar em uma demonstração ao vivo para a banca de jurados.
- **Solução Implementada (SRE):**
  1. Aumento do timeout de leitura de `30s` para `60s` via `httpx.Timeout`.
  2. Implementação de retentativa automática com backoff exponencial de 2 segundos.
  3. Acionamento automático do **Motor Heurístico Clínico Local** em caso de estouro de tempo, garantindo que o usuário nunca receba um erro 500 ou tela em branco.
- **Lição Aprendida:** Sistemas de IA em produção médica precisam de redundância em camadas: o modelo de IA avançado para precisão e um motor determinístico local para garantir disponibilidade de 99.99%.

---

### Desafio 2: Oscilações Transitórias (HTTP 500) em APIs de Terceiros
- **Cenário:** No Cenário 3 (Caso Ambíguo), a API remota da NVIDIA retornou esporadicamente `HTTP 500`.
- **Causa Raiz:** Picos de concorrência ou reinicialização de pods na infraestrutura multi-tenant gratuita da NVIDIA.
- **Impacto:** Perda pontual da resposta da LLM.
- **Solução Implementada (SRE):**
  1. Captura resiliente de códigos de status `[500, 502, 503, 504]` com tentativa de retry antes da desistência.
  2. Degradação graciosa (*graceful degradation*): o sistema identificou que o documento possuía marcas de rasura e ausência de CRM e executou o cálculo de penalidade localmente, roteando com exatidão para a `Fila_Revisao_Humana` e salvando em `auditoria_humana/`.
- **Lição Aprendida:** Arquiteturas orientadas a agentes devem desacoplar a ingestão da inteligência de decisão: a falha de uma LLM externa não pode impedir a auditoria do prontuário.

---

### Desafio 3: Restrições Rígidas da Camada OCI Always Free (Custo Zero)
- **Cenário:** O edital do Hackathon ONE veta estritamente qualquer gasto financeiro, exigindo conformidade total com a camada gratuita vitalícia da Oracle Cloud.
- **Causa Raiz:** Serviços de nuvem podem acidentalmente gerar custos se forem provisionados buckets em excesso ou instâncias pagas.
- **Impacto:** Desclassificação do projeto caso haja cobrança.
- **Solução Implementada (ADR-003):**
  1. Consolidação de todo o armazenamento em **um único bucket** (`mediflow-documentos-clinicos`).
  2. Segregação lógica rigorosa por prefixos (`recebidos/`, `processados/rotina/`, `processados/urgentes/`, `auditoria_humana/`).
  3. Espelhamento local automático em `./oci_bucket_local/`, permitindo desenvolvimento offline sem gastar chamadas de API.
- **Lição Aprendida:** O uso inteligente de namespaces e prefixos em Object Storage substitui a necessidade de múltiplos buckets, simplificando a governança e o controle orçamentário.

---

### Desafio 4: Interpretação de Documentos Clínicos com Baixa Qualidade (Ambiguidade & HitL)
- **Cenário:** Receitas manuscritas digitalizadas com caligrafia ilegível, carimbos borrados ou dados cadastrais faltantes.
- **Causa Raiz:** A heterogeneidade dos documentos na saúde brasileira (papel manual vs. prontuário digital).
- **Impacto:** Risco clínico inaceitável de dispensação errada de medicamentos (ex.: Metoprolol com dose borrada).
- **Solução Implementada:**
  1. Criação de heurísticas de penalização severa no `ValidatorSRECheckNode`: qualquer sinal de rasura ou falta de CRM deduz no mínimo 0.25 do score de confiança.
  2. Trava de segurança: score $< 0.85$ desvia compulsoriamente para a fila de Auditoria Humana (`Fila_Revisao_Humana`), bloqueando a liberação automática.
  3. Interface de 1 clique no Streamlit para que o médico/auditor digite o CRM correto e autorize o documento.
- **Lição Aprendida:** IA na saúde não substitui o médico; ela atua como filtro de triagem inteligente, liberando o que é rotineiro e destacando o que requer julgamento humano.

---

### Desafio 5: Isolamento de Ambiente WSL e Consistência de Trajetória
- **Cenário:** Desenvolvimento em máquina host Windows com execução real no WSL (Ubuntu-24.04).
- **Causa Raiz:** Diferenças de formato de caminho (`\\wsl$\...` vs. `/home/magno/ONE`), quebras de linha (`CRLF` vs. `LF`) e permissões de execução.
- **Impacto:** Possíveis erros de "arquivo não encontrado" ou falhas de pacotes instalados no Windows em vez do Linux.
- **Solução Implementada:**
  1. Assertividade estrita do caminho nativo `/home/magno/ONE` em todos os scripts e comandos.
  2. Uso exclusivo de binários instalados no ambiente Linux (`python3.12`, `uvicorn`, `streamlit`).
  3. Isolamento completo no virtualenv `.venv` dentro do subsistema Linux.
- **Lição Aprendida:** Respeitar as fronteiras do subsistema garante paridade idêntica com o ambiente de produção da nuvem (OCI Linux Compute).

---

### Desafio 6: Migração e Tipagem Formal no LangGraph (`StateGraph`)
- **Cenário:** Transição de uma pipeline sequencial para um grafo de decisão autônomo formal em LangGraph com bifurcações condicionais.
- **Causa Raiz:** O LangGraph exige um estado fortemente tipado (`TypedDict`) e funções de nós que retornem dicionários de atualização parcial sem mutação destrutiva do estado anterior.
- **Impacto:** Erros de compilação de grafo ou perda de telemetria entre transições de nós.
- **Solução Implementada (Carlos Magno - Tech Lead):**
  1. Criação do `MediFlowAgentState(TypedDict)` englobando documento de entrada, entidades extraídas, decisão, armazenamento e telemetria por nó.
  2. Conexão estrita do grafo via `START`, arestas direcionadas para ingestão/classificação/validação e `add_conditional_edges` com a função roteadora `decide_route`.
  3. Exposição do grafo compilado via endpoint REST com geração dinâmica de diagrama Mermaid (`/api/v1/grafo/estrutura`).
- **Lição Aprendida:** A estrutura formal do StateGraph transforma um script procedural em uma máquina de estados visualizável, auditável e defensável perante os jurados do Hackathon.

---

### Desafio 7: Disparo Resiliente de Webhooks Hospitalares sem Bloquear o Fluxo SRE
- **Cenário:** Notificação de emergência médica para equipes de plantão em casos de TEP Agudo via webhook externo.
- **Causa Raiz:** Servidores de webhook de terceiros (Slack, Discord, sistemas hospitalares) podem estar lentos, instáveis ou exigir conexão com a internet que inexiste em testes locais.
- **Impacto:** Bloqueio da thread principal de triagem e violação do SLA de 5.000 ms.
- **Solução Implementada (Fernando Szekut - Fernando Nexus):**
  1. Criação do `NotificationDispatcher` com detecção automática do modo Mock caso a URL não esteja configurada ou o modo de teste esteja ativo.
  2. Configuração de timeout estrito de 3.0s via `httpx.Client`.
  3. Histórico em memória de alertas disparados, permitindo inspeção imediata tanto pela API REST quanto pelos testes automatizados.
- **Lição Aprendida:** Integrações de tempo real em saúde devem ser tratadas de forma desacoplada: a notificação é urgente, mas uma lentidão de rede externa nunca pode atrasar o arquivamento seguro do prontuário no OCI.

---

## 2. 🛡️ Matriz de Riscos e Mitigações Futuras

| Risco Identificado | Probabilidade | Impacto | Estratégia de Mitigação |
| :--- | :--- | :--- | :--- |
| **Esgotamento da cota de créditos gratuitos da NVIDIA** | Média | Alta | Ativação instantânea do Gemini 2.0 Flash (15 RPM free) ou fallback local heurístico. |
| **Queda de conectividade durante a gravação da Demo** | Baixa | Crítica | O espelho local SRE (`./oci_bucket_local`) e o fallback garantem demonstração completa sem internet. |
| **Alucinação de código CID-10 pela LLM** | Média | Média | Validador sintático via regex e tabela estática de códigos críticos de urgência (I26.9 para TEP, I21.9 para IAM). |

