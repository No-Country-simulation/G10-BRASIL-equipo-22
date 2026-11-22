# 🎬 MediFlow — Roteiro Técnico do Vídeo de Demonstração (3 Minutos)
**Desafio:** Hackathon ONE G10 — Oracle Next Education & Alura  
**Squad:** Equipo 22  
**Duração Alvo:** Estritamente 03:00 (180 segundos)  
**Formato de Saída:** 1080p (Full HD, 60fps), Áudio Normalizado (-14 LUFS)  
**Voz/Apresentação:** Carlos Magno (Tech Lead) & Fernando Szekut (UX/Agent Integration)  

---

## ⏱️ Linha do Tempo & Bloco a Bloco

### [00:00 - 00:30] Bloco 1: O Problema Clínico e a Solução MediFlow
- **Visual:** Gravação de tela com prontuários empilhados, títulos de notícias sobre glosas e erros de transcrição, transicionando para o logo e arquitetura do MediFlow.
- **Áudio / Fala:**
  > *"Hospitais e operadoras de saúde recebem milhares de documentos heterogêneos todos os dias: receitas manuscritas, laudos de radiologia, guias TISS e relatórios cirúrgicos. A triagem manual gera glosas milionárias, atrasos administrativos e, pior, riscos fatais quando um laudo grave passa desapercebido na fila.*  
  > *Apresentamos o **MediFlow**: um agente autônomo inteligente projetado para ingerir, extrair entidades clínicas, detectar urgências em tempo real e rotear documentos com confiabilidade de produção na Oracle Cloud."*

---

### [00:30 - 01:00] Bloco 2: Arquitetura LangGraph & Ingestão Multimodal
- **Visual:** Diagrama interativo do LangGraph StateGraph em execução, mostrando os nós de Ingestão (`mediflow_ingestao.py`), Classificação com Fast-Path heurístico (<50ms) e Fallback multimodal NVIDIA NIM / Gemini.
- **Áudio / Fala:**
  > *"Nossa arquitetura é orquestrada por um grafo de estados determinístico no LangGraph. Para documentos padronizados, implementamos um motor de Fast-Path em autômatos regex pré-compilados que realiza a triagem em submilisegundos. Para casos complexos ou manuscritos, conectamos modelos multimodais de visão computacional, garantindo extração tipada de diagnósticos, CID-10, dados do paciente e CRM médico sob validação Pydantic v2."*

---

### [01:00 - 01:45] Bloco 3: Demonstração ao Vivo no Streamlit (Os 3 Fluxos)
- **Visual:** Gravação de tela do painel web Streamlit (`app.py`), demonstrando os 3 cenários clínicos em tempo real:
  1. **Cenário 1 (Rotina):** Receita ambulatorial com amoxicilina. Ingestão instantânea, score 0.95, aprovação automática para Farmácia e Prontuário Eletrônico.
  2. **Cenário 2 (Urgência Crítica TEP):** Laudo radiológico com Tromboembolismo Pulmonar Agudo. Badge vermelho Manchester pulsante, alerta sonoro sintetizado em tempo real e disparo imediato de Webhook para a equipe de plantão de emergência.
  3. **Cenário 3 (HitL Ambíguo):** Receita com rasura e CRM ilegível. Score penalizado para 0.15, retido na fila de Human-in-the-Loop. Visualizador lado a lado com PDF original e campos editáveis; clique do médico auditor para homologação instantânea.
- **Áudio / Fala:**
  > *"No painel clínico do Streamlit, vemos os três fluxos canônicos em ação:  
  > Primeiro, uma receita de rotina é aprovada automaticamente sem intervenção humana.  
  > Segundo, um laudo de Tromboembolismo Pulmonar Agudo dispara o protocolo Manchester de emergência com badge pulsante, alerta sonoro e notificação imediata via webhook para a equipe de plantão.  
  > Terceiro, um documento com rasuras é direcionado à auditoria Human-in-the-Loop, onde o médico auditor compara o documento original no visualizador multimodal e aprova com apenas um clique."*

---

### [01:45 - 02:30] Bloco 4: Engenharia SRE, Resiliência e Oracle Cloud (OCI)
- **Visual:** Terminal executando `week6/demo_runner.py` e testes de carga em `week4/`. Transição para o console OCI mostrando os buckets Always Free particionados dinamicamente (`processados/urgentes/`, `processados/rotina/`, `auditoria_humana/`).
- **Áudio / Fala:**
  > *"Na camada de infraestrutura e confiabilidade SRE, o MediFlow é blindado para produção:  
  > Nosso Circuit-Breaker garante Zero Downtime: se a API backend sofrer degradação, o sistema chaveia automaticamente para o motor in-process sem perder nenhuma requisição.  
  > Nossos testes de carga comprovam uma vazão de 90 requisições por segundo com 100% de conformidade de SLA e p99 abaixo de 50 milissegundos.  
  > E no armazenamento em nuvem, integramos o Oracle Cloud Infrastructure Object Storage na camada Always Free, com segregação dinâmica por especialidade e conformidade orçamentária comprovada com custo de zero reais."*

---

### [02:30 - 03:00] Bloco 5: Qualidade de Código, Cobertura e Conclusão
- **Visual:** Tela do terminal com o pytest executando 174+ testes automatizados (100% passing) e relatório de cobertura >= 90%. Slide de encerramento com membros da equipe (Equipo 22), repositório GitHub e QR Code.
- **Áudio / Fala:**
  > *"O projeto conta com mais de 170 testes automatizados, cobertura superior a 90% nos módulos críticos e pipeline de CI/CD rigoroso.  
  > O MediFlow une IA multimodal, orquestração de ponta e engenharia de confiabilidade de classe mundial para salvar vidas e transformar a saúde digital.  
  > Muito obrigado ao time Alura e Oracle pelo Desafio ONE G10!"*
