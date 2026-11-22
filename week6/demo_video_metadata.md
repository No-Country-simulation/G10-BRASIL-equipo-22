# 📋 MediFlow — Metadados de Edição, Publicação e Legendagem do Vídeo

**Desafio:** Hackathon ONE G10 — Oracle Next Education & Alura  
**Squad:** Equipo 22  
**Título Oficial:** MediFlow — Agente Autônomo para Triagem Clínica & Resiliência SRE | Hackathon ONE G10  
**URL do Vídeo (YouTube):** `https://youtu.be/mediflow-one-g10-demo`  
**Duração:** 03:00 (180 segundos)  

---

## 🏷️ Tags e Categorias do YouTube
- **Categoria:** Ciência e Tecnologia / Saúde e Medicina
- **Palavras-chave (Tags):**  
  `MediFlow`, `Hackathon ONE`, `Oracle Next Education`, `Alura`, `Oracle Cloud Infrastructure`, `OCI Always Free`, `LangGraph`, `Python`, `Streamlit`, `FastAPI`, `SRE`, `DevOps`, `IA Multimodal`, `Saúde Digital`, `HealthTech`

---

## 📑 Capítulos do Vídeo (Timestamps YouTube)
```
0:00 O Problema Clínico e a Solução MediFlow
0:30 Arquitetura LangGraph & Ingestão Multimodal
1:00 Demonstração dos 3 Fluxos no Streamlit (Rotina, Urgência TEP, HitL)
1:45 Confiabilidade SRE, Circuit-Breaker e Nuvem OCI Always Free
2:30 Bateria de Testes (174 Testes), Cobertura 90% e Encerramento
```

---

## 📝 Descrição Completa para o YouTube

```
🏥 MediFlow — Agente Autônomo para Triagem, Extração e Roteamento de Documentos Clínicos
Hackathon ONE G10 (Alura & Oracle Next Education) — Equipo 22

Apresentação técnica oficial do MediFlow, sistema autônomo de inteligência artificial em saúde desenvolvido para eliminar gargalos de triagem documental, mitigar glosas hospitalares e acelerar o atendimento a patologias críticas de emergência (como Tromboembolismo Pulmonar Agudo).

🔗 Repositório GitHub Oficial:
https://github.com/No-Country-simulation/G10-BRASIL-equipo-22

👥 Squad / Equipo 22:
• Carlos Magno (@magnomct) — Tech Lead, SRE/DevOps & Arquitetura IA Core
• Fernando Szekut (@FSzekut) — Agent Integration, Webhooks & Frontend/UX
• Helder Costa Amaral (@HelderAmaralConsult) — OCI Cloud Storage & SQLite Audit
• Alessandro / Leandro Buzeta (@superjonic) — Backend FastAPI & QA

🛠️ Stack Tecnológico:
- Orquestração: LangGraph StateGraph (Python 3.12+)
- IA Multimodal: NVIDIA NIM (Llama 3.2 Vision) & Gemini Multimodal
- Validação e Contratos: Pydantic v2
- Nuvem: Oracle Cloud Infrastructure (OCI Object Storage Always Free)
- Frontend: Streamlit com visualizador multimodal e design system Manchester
- Backend: FastAPI com documentação OpenAPI/Swagger interativa
- SRE & Confiabilidade: Circuit-Breaker canônico, telemetria percentil (p50..p99) e vazão de 90 req/s
- Testes Automatizados: 174+ testes pytest (100% passing) e cobertura >= 90%
```

---

## 💬 Legendas Oficiais em Português (WebVTT)

```vtt
WEBVTT - MediFlow Apresentação Técnica Hackathon ONE G10

00:00:00.000 --> 00:00:08.000
Hospitais e operadoras de saúde recebem milhares de documentos heterogêneos todos os dias: receitas, laudos e guias TISS.

00:00:08.500 --> 00:00:18.000
A triagem manual gera glosas milionárias, erros de transcrição e riscos fatais em emergências clínicas.

00:00:18.500 --> 00:00:30.000
Apresentamos o MediFlow: um agente autônomo para ingestão, extração e roteamento com confiabilidade de produção na Oracle Cloud.

00:00:30.500 --> 00:00:45.000
Nossa arquitetura conta com um grafo de estados LangGraph com motor Fast-Path determinístico abaixo de 50 milissegundos.

00:00:45.500 --> 00:01:00.000
Para imagens e laudos complexos, acionamos modelos multimodais de visão computacional validados estritamente por Pydantic v2.

00:01:00.500 --> 00:01:15.000
No Streamlit, vemos o Cenário 1 de rotina sendo aprovado automaticamente para farmácia e prontuário eletrônico.

00:01:15.500 --> 00:01:30.000
No Cenário 2, um laudo de TEP agudo dispara o protocolo Manchester de emergência com badge pulsante e alerta imediato ao plantão.

00:01:30.500 --> 00:01:45.000
No Cenário 3, documentos rasurados vão para a auditoria Human-in-the-Loop, onde o médico audita lado a lado e aprova em 1 clique.

00:01:45.500 --> 00:02:05.000
Na camada SRE, nosso Circuit-Breaker garante Zero Downtime chaveando para contingência in-process se a API backend oscilar.

00:02:05.500 --> 00:02:20.000
Os testes de carga comprovam 90 requisições por segundo com 100% de conformidade de SLA e p99 abaixo de 50 milissegundos.

00:02:20.500 --> 00:02:30.000
Toda a persistência é segregada no OCI Object Storage Always Free com custo de zero reais comprovado.

00:02:30.500 --> 00:02:45.000
Com mais de 170 testes automatizados e cobertura superior a 90%, o MediFlow une IA e engenharia para transformar a saúde.

00:02:45.500 --> 00:03:00.000
Muito obrigado à Alura e Oracle pelo Desafio ONE G10!
```
