# 🎙️ MediFlow — Roteiro de Introdução em Vídeo: Contextualização do Problema e Solução

**Projeto:** MediFlow — Agente Autônomo para Triagem, Extração e Roteamento de Documentos Clínicos  
**Desafio:** Hackathon ONE G10 — Oracle Next Education & Alura  
**Squad:** Equipo 22  
**Finalidade:** Guia de fala e gravação para a abertura do vídeo de pitch/demonstração  

---

## 1. O Problema Real na Saúde Brasileira (SUS & Saúde Suplementar)

- Mais de **300 milhões** de documentos clínicos físicos e digitais transitam anualmente entre hospitais, clínicas e operadoras de saúde no Brasil.
- **Gargalo Operacional:** Médicos, enfermeiros e auditores gastam até 35% de sua jornada de trabalho transcrevendo dados de receitas, relatórios de alta e pedidos de autorização TISS/TUSS.
- **Impacto Financeiro:** Taxas de glosa hospitalar (recusa de faturamento por inconsistência documental) superam 15% a 22% no setor privado, gerando bilhões de reais em atrasos e prejuízos.
- **Risco de Vida (O Ponto Crítico):** Quando um paciente em pronto-socorro realiza uma tomografia com suspeita de Tromboembolismo Pulmonar Agudo (TEP) ou Infarto Agudo do Miocárdio (IAM), o laudo muitas vezes fica aguardando digitação ou triagem em uma fila comum. Minutos de atraso na identificação de um achado grave são a diferença entre a vida e o óbito do paciente.

---

## 2. A Resposta do MediFlow

O **MediFlow** foi concebido não apenas como um leitor de documentos, mas como um **Agente Clínico Autônomo de Produção**:
1. **Ingestão Universal:** Lê receitas em PDF, fotos de celulares de receitas médicas amassadas, laudos laboratoriais e guias TISS.
2. **Triagem em Submilisegundos:** Combina um motor heurístico Fast-Path (<50ms) com modelos de visão computacional multimodal de ponta (NVIDIA NIM / Gemini).
3. **Segurança do Paciente em Primeiro Lugar:** Detecta achados críticos e aciona o protocolo Manchester imediatamente, notificando a equipe de plantão via webhooks e banners sonoros.
4. **Governança Human-in-the-Loop:** Quando há rasura, ambiguidade ou score de confiança abaixo de 0.85, o documento é retido para revisão humana em 1 clique, impedindo alucinações da IA de entrarem no prontuário.
5. **Nuvem Oracle Always Free:** Todos os documentos são arquivados de forma auditável e segregada no OCI Object Storage com custo de infraestrutura zero reais.

---

## 3. Mensagem de Fechamento da Introdução

> *"O MediFlow devolve o tempo do médico para o que realmente importa: cuidar do paciente. Mais do que automação, trazemos confiabilidade, velocidade e precisão para salvar vidas com o poder da Inteligência Artificial e da Oracle Cloud."*
