Programa ONE · Grupo 10 | Agente Autônomo para Triagem, ...

Projeto 2 – 🏥 MediFlow – Agente Autônomo para

Triagem, Extração e Roteamento de Documentos

Clínicos

Mapeamento de Formações ONE (Grupo 10)

•  Formações Indispensáveis: Engenharia de Agentes e Automação e Oracle Cloud Infrastructure (OCI).
•  Formações de Reforço: Desarrollo y Orquestación con IA Generativa.
•  Núcleo Técnico: Grafo de decisão condicional para classificação, extração precisa de dados clínicos
e tratamento de ambiguidades/urgências (Human-in-the-Loop), automação de fluxos e segregação
de arquivos no OCI Object Storage na camada Always Free.

Setor empresarial

HealthTech / Gestão Hospitalar / Operadoras de Saúde & Clínicas Médicas — Soluções

tecnológicas aplicadas ao processamento, auditoria e triagem de fluxos documentais em saúde. O setor

lida diariamente com milhares de documentos heterogêneos (laudos médicos, receitas, guias de

autorização TISS/TUSS, pedidos de exames complementares e relatórios cirúrgicos), nos quais a

precisão das informações e a agilidade no encaminhamento são determinantes para a segurança do
paciente e a eficiência operacional.

Descrição do projeto

Desenvolver um agente inteligente e autônomo capaz de receber documentos clínicos e administrativos

em múltiplos formatos (arquivos PDF digitalizados, imagens de exames/receitas ou textos), classificá-los

automaticamente, extrair entidades e dados clínicos essenciais com altíssima precisão e roteá-los para o
destino correto sem necessidade de intervenção humana manual para casos padrão.

O processamento documental na área da saúde exige rigor absoluto. A solução MediFlow deve

resolver desafios complexos de visão multimodal, extração estruturada de dados clínicos, lógica de

decisão condicional e tratamento de casos ambíguos ou urgentes (como dados ilegíveis, prescrições
de alto risco ou solicitações de urgência).

A aplicação deverá:

1. Ingerir o documento clínico nos formatos suportados (PDF / Imagem / JSON);

2. Identificar e classificar a categoria do documento (ex.: Receituário Médico, Laudo de Exame

Laboratorial/Imagem, Guia de Solicitação de Procedimento, Relatório de Alta/Internação, Atestado
Médico);

3. Extrair dados clínicos e administrativos essenciais (identificação do paciente, dados do

profissional/CRM, hipótese diagnóstica/CID-10, medicamentos, dosagens, urgência, exames

Hackathon ONE G10 — Oracle Next Education & Alura

Programa ONE · Grupo 10 | Agente Autônomo para Triagem, ...

solicitados) utilizando LLMs de escolha da equipe (Google Gemini, OpenAI, Claude ou outros
modelos);

4. Avaliar consistência, potenciais conflitos e score de confiabilidade da extração;

5. Executar a lógica de roteamento automatizado para o departamento de destino (ex.: Fila de

Urgência Médica, Auditoria de Autorizações, Farmácia Hospitalar, Prontuário Eletrônico do Paciente
ou Fila de Revisão Humana em caso de ambiguidade).

Os resultados e o histórico de triagem deverão ser disponibilizados em formato JSON estruturado, e a

persistência dos documentos e decisões deve ser integrada ao OCI Object Storage (camada Always
Free).

Necessidade do cliente (explicação não técnica)

Hospitais, laboratórios e operadoras de saúde perdem milhares de horas com equipes administrativas

lendo manualmente laudos e receitas para digitar dados em sistemas legados. Além de lento e custoso,

esse processo manual está sujeito a erros graves de digitação e atrasos no atendimento a pacientes
com quadros de urgência.

A solução deve permitir:

•  Receber documentos em qualquer formato (PDFs digitais ou digitalizados);
•  Compreender imediatamente o tipo de documento e seu nível de prioridade clínica;
•  Extrair com precisão cirúrgica os dados vitais (medicamentos, diagnósticos, médicos solicitantes);
•

Identificar casos ambíguos ou dados faltantes, sinalizando imediatamente para um auditor
humano (Human-in-the-Loop);

•  Encaminhar os dados automaticamente para os sistemas de destino, acelerando autorizações e

atendimentos.

Validação de mercado

O mercado de automação em saúde (HealthTech Document Automation & Clinical NLP) é um dos
setores que mais atrai investimentos em IA:

•  Falhas e atrasos em autorizações de exames e medicamentos geram prejuízos bilionários em glosas

hospitalares e impactam diretamente o tratamento dos pacientes.

•  Soluções baseadas em agentes autônomos com LLMs multimodais superam amplamente os

OCRs tradicionais, pois são capazes de interpretar o contexto clínico, validar consistência e tomar
decisões de roteamento inteligentes.

•  A capacidade de operar com fluxos de Human-in-the-Loop oferece a segurança regulatória

necessária para adoção imediata em ambientes de saúde.

Objetivo do Hackathon

Desenvolver um MVP funcional de agente autônomo capaz de:

1. Receber documentos clínicos e administrativos em PDF, imagem ou texto;

Hackathon ONE G10 — Oracle Next Education & Alura

Programa ONE · Grupo 10 | Agente Autônomo para Triagem, ...

2. Utilizar LLMs multimodais (Google Gemini, OpenAI GPT-4o, Claude ou equivalentes) para
interpretar o documento e extrair entidades estruturadas;

3. Implementar um grafo de decisão com nós condicionais (via LangGraph, n8n ou código Python
equivalente) para classificar o documento, avaliar a confiança e rotear para o destino correto;

4. Tratar casos ambíguos, inconsistentes ou urgentes com regras de contingência e alertas de
revisão humana;

5. Persistir os documentos em buckets organizados no OCI Object Storage (camada Always Free);

6. Disponibilizar uma interface de triagem ou API REST para visualização dos fluxos.

Resultados esperados

1. IA Multimodal, Agentes & Lógica de Decisão

Notebook ou módulos contendo:

•  Pipeline de ingestão e processamento de documentos clínicos (PDFs/Imagens);
•  Extração de entidades estruturadas utilizando LLMs/Multimodalidade;
•  Modelagem do fluxo de decisão como um Grafo de Agentes (LangGraph), Workflow n8n com
nós de IA ou pipeline condicional em Python com ramificações (Conditional Edges / nós IF);

•  Mecanismo de cálculo de score de confiança e detecção de urgências médicas.

2. Automação de Fluxos & Back-End

Aplicação em Python (Streamlit / Gradio / FastAPI / Flask) ou fluxo em n8n contendo:

•  Endpoint ou tela para envio de documentos clínicos;
•  Execução do fluxo de triagem e roteamento automatizado;
•  Tratamento de exceções e fallback para revisão humana quando o score de confiança for baixo;
•  Estruturação de dados clínicos no formato JSON validado com Pydantic ou JSON Schema.

3. Oracle Cloud Infrastructure (OCI) — Camada Always Free

•  Requisito Obrigatório (MVP): OCI Object Storage — Buckets segregados para armazenamento

dos documentos recebidos e organização por status (ex.: /recebidos, /processados,
/auditoria_humana);

•  Recurso Opcional / Diferencial: OCI Compute Instance ("Deploy Completo em Nuvem") —

Hospedagem da aplicação ou container n8n em máquina virtual Always Free da OCI;

•  Aviso Importante ONE: Em respeito à natureza social e 100% gratuita do programa ONE, utilize

exclusivamente os recursos Always Free da OCI.

4. Documentação & Demonstração

•  Repositório Git com commits bem documentados;
•  README.md com arquitetura, diagrama do fluxo de decisão do agente e instruções de execução;
•  Demonstração prática cobrindo pelo menos três casos de teste: (1) Fluxo padrão aprovado, (2)

Caso com prioridade de urgência médica e (3) Caso ambíguo direcionado para auditoria humana.

Hackathon ONE G10 — Oracle Next Education & Alura

Programa ONE · Grupo 10 | Agente Autônomo para Triagem, ...

Funcionalidades obrigatórias (MVP)

Endpoint / Fluxo: Processamento e Triagem Clínica

O sistema deve receber um documento clínico, processá-lo pelo agente e retornar o diagnóstico de
triagem com os dados extraídos e a decisão de roteamento.

Exemplo de Requisição (Entrada):

{
  "documento_id": "DOC-CLIN-2026-8942",
  "tipo_arquivo": "PDF",
  "documento_texto": "HOSPITAL SANTA LUCIA - LAUDO DE EXAME RADIOLOGICO. Paciente: Carlos
Eduardo Mendes, 52 anos. Solicitante: Dra. Renata Silveira CRM-SP 145892. Exame: Tomografia
de Torax com contraste. Indicacao: Suspeita de embolia pulmonar aguda, dispneia subita.
Achados: Falha de enchimento em arteria pulmonar principal direita compativel com TEP agudo.
CONCLUSÃO: Quadro compativel com Tromboembolismo Pulmonar Agudo. Sugere-se correlacao clinica
urgente.",
  "canal_origem": "Pronto_Socorro"
}

Exemplo de Resposta (Saída Estruturada):

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
    "justificativa_roteamento": "Achado critico de alta gravidade (TEP agudo) detectado em
paciente sintomatico.",
    "notificacao_gerada": {

Hackathon ONE G10 — Oracle Next Education & Alura

Programa ONE · Grupo 10 | Agente Autônomo para Triagem, ...

      "canal": "Alerta_Plantao_Medico",
      "mensagem": "ALERTA URGENTE: Laudo critico de TEP Agudo para paciente Carlos Eduardo
Mendes no Pronto-Socorro."
    }
  },
  "armazenamento_oci": {
    "bucket": "mediflow-documentos-clinicos",
    "caminho_objeto": "processados/urgentes/DOC-CLIN-2026-8942.json",
    "status_backup": "sucesso"
  }
}

Requisitos mínimos (Checklist de Avaliação)

•  ☐  Ingestão funcional de documentos clínicos em texto ou PDF/imagem;

•  ☐  Classificação automática de tipo de documento clínico com LLMs/Multimodalidade (Google

Gemini, OpenAI, Claude ou equivalentes);

•  ☐  Extração precisa de dados clínicos essenciais em formato estruturado (JSON);

•  ☐  Implementação de lógica de decisão condicional com tratamento de casos ambíguos ou

urgentes (LangGraph, n8n ou código Python);

•  ☐  Integração ativa com o OCI Object Storage (camada Always Free) para segregação e

armazenamento dos documentos;

•  ☐  Demonstração de no mínimo 3 cenários distintos (Rotina, Urgência e Ambiguidade/Erro

direcionado para revisão humana);

•  ☐  Documentação completa no repositório GitHub com diagrama do fluxo do agente.

Recursos opcionais (Diferenciais)

•  Fluxo Clínico Customizável pelo Usuário: Módulo ou interface que permita ao gestor hospitalar
configurar regras de triagem personalizadas, novos destinos de roteamento e limites de urgência
sem mexer no código-fonte;

•  Deploy Completo em Nuvem (OCI Compute): Hospedagem da aplicação ou container n8n em

máquina virtual Always Free da OCI com acesso público;

•  OCR e Visão Computacional Multimodal: Leitura direta de fotos de receitas manuscritas ou

laudos escaneados;

•  Painel de Auditoria Human-in-the-Loop em Streamlit: Interface visual onde auditores clínicos
podem visualizar documentos com baixa confiança e aprovar/rejeitar a extração com um clique;

•  Alertas em Tempo Real: Workflow no n8n disparando alertas no Slack/Email para equipes de

plantão.

Hackathon ONE G10 — Oracle Next Education & Alura

Programa ONE · Grupo 10 | Agente Autônomo para Triagem, ...

Diretrizes técnicas para os estudantes

IA Generativa & Agentes Autônomos

•  Modelos de Linguagem: As equipes podem utilizar livremente Google Gemini, OpenAI (ChatGPT
/ GPT-4o), Anthropic (Claude) ou outras LLMs (o Gemini é a ferramenta ensinada no curso, mas
qualquer LLM equivalente é permitida);

•  Orquestração de Agentes: Sugere-se o uso de LangGraph para grafos de decisão ou n8n com nós
de IA; arquiteturas em Python puro ou outros frameworks de agentes (ex.: CrewAI) também são
totalmente aceitas;

•  Validação de Dados: Recomenda-se Pydantic para validar tipagens e consistência clínica.

Automação & Interface

•  Tecnologias Sugeridas: n8n para automações de fluxo e Streamlit ou Gradio para telas de

triagem; soluções em Node.js ou frameworks web equivalentes são permitidas.

Oracle Cloud Infrastructure (OCI)

•  Object Storage (Obrigatório): Crie buckets Always Free para armazenar e organizar os

documentos por status;

•  Atenção aos Custos: Mantenha a utilização restrita aos recursos da camada Always Free.

Hackathon ONE G10 — Oracle Next Education & Alura


