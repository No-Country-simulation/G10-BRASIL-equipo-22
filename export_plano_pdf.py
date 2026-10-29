#!/usr/bin/env python3
"""
MediFlow — Script de Exportação do Plano de Projeto para PDF Executivo
Hackathon ONE G10 — Oracle Next Education & Alura (Equipo 22)
Equipe: Carlos Magno (Tech Lead & SRE), Fernando Szekut, Helder, Alessandro
"""

import os
from fpdf import FPDF
from fpdf.fonts import FontFace
from fpdf.enums import XPos, YPos


class MediFlowPDF(FPDF):
    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.set_margins(15, 14, 15)
        self.set_auto_page_break(auto=True, margin=14)

        # Fontes DejaVu com suporte total a UTF-8 (acentos em Português)
        font_dir = "/usr/share/fonts/truetype/dejavu"
        self.add_font("DejaVu", "", os.path.join(font_dir, "DejaVuSans.ttf"))
        self.add_font("DejaVu", "B", os.path.join(font_dir, "DejaVuSans-Bold.ttf"))

    def header(self):
        if self.page_no() > 1:
            self.set_font("DejaVu", "", 7.5)
            self.set_text_color(100, 116, 139)  # Slate 500
            self.cell(0, 5, "MediFlow — Plano Executivo & Cronograma | Hackathon ONE G10 (Equipo 22)", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.set_draw_color(226, 232, 240)
            self.set_line_width(0.3)
            self.line(15, 15, 195, 15)
            self.ln(2)

    def footer(self):
        self.set_y(-12)
        self.set_font("DejaVu", "", 7.5)
        self.set_text_color(148, 163, 184)
        self.set_draw_color(226, 232, 240)
        self.line(15, 285, 195, 285)
        self.cell(0, 6, f"Documento Interno de Engenharia — Equipo 22 | Página {self.page_no()} de {{nb}}", align="C")

    def chapter_title(self, title):
        self.ln(2)
        self.set_fill_color(241, 245, 249)  # Slate 100
        self.set_draw_color(14, 116, 144)   # Cyan 700
        self.set_line_width(0.8)
        self.set_font("DejaVu", "B", 10.5)
        self.set_text_color(15, 23, 42)      # Slate 900
        self.cell(0, 7.5, f"  {title}", fill=True, border="L", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(2)

    def section_title(self, title):
        self.ln(1)
        self.set_font("DejaVu", "B", 9)
        self.set_text_color(30, 58, 138)    # Blue 900
        self.cell(0, 5.5, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(0.5)

    def body_text(self, text):
        self.set_font("DejaVu", "", 8)
        self.set_text_color(51, 65, 85)     # Slate 700
        self.multi_cell(0, 4.2, text)
        self.ln(1)

    def quote_box(self, text):
        self.set_fill_color(248, 250, 252)  # Slate 50
        self.set_draw_color(203, 213, 225)
        self.set_font("DejaVu", "", 7.8)
        self.set_text_color(71, 85, 105)
        self.multi_cell(0, 3.8, f"   \"{text}\"", fill=True, border="L")
        self.ln(1.5)


def generate_pdf():
    pdf = MediFlowPDF()
    pdf.alias_nb_pages()

    # =========================================================================
    # PÁGINA 1: CAPA, METADADOS E TABELA DAS 4 PERSONAS
    # =========================================================================
    pdf.add_page()

    # Banner Capa
    pdf.set_fill_color(15, 23, 42)  # Dark Navy #0F172A
    pdf.rect(15, 14, 180, 32, style="F")

    pdf.set_xy(20, 18)
    pdf.set_font("DejaVu", "B", 13.5)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 7, "[+] MediFlow — Plano Executivo & Cronograma", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_x(20)
    pdf.set_font("DejaVu", "", 8.5)
    pdf.set_text_color(148, 163, 184)
    pdf.cell(0, 4.5, "Agente Autônomo para Triagem, Extração e Roteamento de Documentos Clínicos", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_x(20)
    pdf.set_font("DejaVu", "B", 7.5)
    pdf.set_text_color(56, 189, 248)  # Cyan 400
    pdf.cell(0, 5, "Hackathon ONE G10 · Oracle Next Education & Alura | Squad: Equipo 22", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_y(50)

    # Metadados
    pdf.set_font("DejaVu", "", 8)
    pdf.set_text_color(51, 65, 85)
    pdf.cell(0, 4.2, "• Equipe: Carlos Magno (Tech Lead & SRE), Fernando Szekut (Frontend/Workflows), Helder (OCI) e Alessandro (Backend/QA)", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 4.2, "• Posição Atual: Semana 3 de 6 (Milestone 3: Grafo Condicional LangGraph, Workflows & OCI Always Free)", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 4.2, "• Stack: Python 3.12+ · LangGraph · Pydantic v2 · NVIDIA NIM Llama 3.2 11B Vision · OCI Always Free", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)

    # Seção 1
    pdf.chapter_title("1. Arquitetura das 4 Personas Técnicas Especialistas (Equipo 22)")
    pdf.body_text(
        "Alinhando as personas técnicas aos talentos complementares do time de 4 pessoas "
        "(Carlos Magno, Fernando Szekut, Helder e Alessandro), estruturamos 4 Personas Especialistas:"
    )

    headings = ["Persona Especialista", "Papel Integrado", "Integrante Responsável", "Foco Prático no MediFlow"]
    col_widths = [36, 42, 40, 62]

    with pdf.table(
        col_widths=col_widths,
        borders_layout="SINGLE_TOP_LINE",
        headings_style=FontFace(color=(255, 255, 255), fill_color=(30, 41, 59), emphasis="BOLD"),
        line_height=4.2,
    ) as table:
        row = table.row()
        for h in headings:
            row.cell(h)

        # Carlos
        row = table.row()
        row.cell("Persona 1:\nArquiteto Carlos Vance")
        row.cell("Tech Lead, Líder SRE/DevOps,\nArquitetura IA & Python Core")
        row.cell("Carlos Magno\n(Tech Lead & SRE)\ngithub.com/magnomct")
        row.cell("Governança técnica, LangGraph StateGraph, schemas Pydantic, motor NVIDIA NIM, CI/CD Actions e resiliência local SRE.")

        # Fernando
        row = table.row()
        row.cell("Persona 2:\nFernando Nexus")
        row.cell("Engenheiro de Integração,\nFrontend/UX & Workflows")
        row.cell("Fernando Szekut\n(Frontend/Workflows)\ngithub.com/FSzekut")
        row.cell("Usabilidade do Dashboard Streamlit, visualizador de laudos, ingestão de imagens/PDFs e Webhooks de plantão médico em tempo real.")

        # Helder
        row = table.row()
        row.cell("Persona 3:\nAtlas Data")
        row.cell("Especialista em Banco de Dados,\nPersistência OCI Always Free")
        row.cell("Helder\n(Dados & OCI Always Free)")
        row.cell("Segregação de buckets OCI Always Free (/recebidos, /processados, /auditoria_humana), modelo relacional e custo zero.")

        # Alessandro
        row = table.row()
        row.cell("Persona 4:\nMarcus Builder")
        row.cell("Desenvolvedor Backend FastAPI,\nMódulo HitL & QA")
        row.cell("Alessandro\n(Backend FastAPI & QA)")
        row.cell("Endpoints REST oficiais (/api/v1/triagem, /auditoria), fluxo de Auditoria Humana HitL, Kanban GitHub e Vídeo Demo.")

    # =========================================================================
    # PÁGINA 2: DETALHAMENTO DAS PERSONAS (PROMPTS) & MATRIZ RACI
    # =========================================================================
    pdf.add_page()
    pdf.chapter_title("1.1 Links Profissionais e System Prompts das 4 Personas")

    pdf.set_font("DejaVu", "B", 8)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 4.2, "[Persona 1] Arquiteto Carlos Vance (Carlos Magno - Tech Lead & SRE):", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("DejaVu", "", 7.5)
    pdf.set_text_color(37, 99, 235)
    pdf.cell(0, 3.8, "   • GitHub: https://github.com/magnomct | Portfólio: https://carlosmagnocloudengineer.vercel.app/en", new_x=XPos.LMARGIN, new_y=YPos.NEXT, link="https://carlosmagnocloudengineer.vercel.app/en")
    pdf.quote_box(
        "Você é o Arquiteto Carlos Vance, Tech Lead e Líder de SRE/DevOps, Arquitetura de IA e Python do projeto MediFlow. "
        "Sua prioridade é assegurar a excelência técnica da solução, pipelines robustos em LangGraph e Pydantic, SLAs rigorosos "
        "de latência, observabilidade, resiliência contra falhas e zero falso-negativo em emergências médicas (como TEP Agudo)."
    )

    pdf.set_font("DejaVu", "B", 8)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 4.2, "[Persona 2] Fernando Nexus (Fernando Szekut - Frontend & Agent Integration):", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("DejaVu", "", 7.5)
    pdf.set_text_color(37, 99, 235)
    pdf.cell(0, 3.8, "   • GitHub: https://github.com/FSzekut | Portfólio: https://fernando-szekut.netlify.app/", new_x=XPos.LMARGIN, new_y=YPos.NEXT, link="https://fernando-szekut.netlify.app/")
    pdf.quote_box(
        "Você é Fernando Nexus, Engenheiro de Integração de Agentes, Frontend/UX e Automação de Workflows do MediFlow. "
        "Sua prioridade é projetar interfaces clínicas claras, enriquecer o pipeline multimodal e garantir que decisões do agente "
        "e alertas críticos cheguem com agilidade visual aos profissionais de saúde."
    )

    pdf.set_font("DejaVu", "B", 8)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 4.2, "[Persona 3] Atlas Data (Helder - Banco de Dados & OCI Always Free):", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.quote_box(
        "Você é Atlas Data, Especialista em Banco de Dados e Persistência OCI do MediFlow. Sua prioridade é estruturar a modelagem "
        "dos dados clínicos em JSON estruturado e tabelas relacionais, organizar a segregação de objetos no OCI Object Storage Always Free "
        "e garantir rastreabilidade completa com custo zero."
    )

    pdf.set_font("DejaVu", "B", 8)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 4.2, "[Persona 4] Marcus Builder (Alessandro - Backend FastAPI, HitL & QA):", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.quote_box(
        "Você é Marcus Builder, Desenvolvedor Backend e QA do MediFlow. Seu objetivo é assegurar rotas REST rápidas e padronizadas, "
        "operacionalizar a tela de auditoria humana em conjunto com Fernando e validar todos os cenários de teste."
    )

    # Seção 2: Matriz RACI
    pdf.chapter_title("2. Matriz de Responsabilidades (RACI) do Equipo 22")
    col_raci = [45, 45, 90]
    with pdf.table(
        col_widths=col_raci,
        borders_layout="SINGLE_TOP_LINE",
        headings_style=FontFace(color=(255, 255, 255), fill_color=(30, 41, 59), emphasis="BOLD"),
        line_height=4.2,
    ) as table:
        row = table.row()
        row.cell("Integrante & Links")
        row.cell("Persona & Perfil")
        row.cell("Entregas Técnicas no Repositório")

        row = table.row()
        row.cell("Carlos Magno (Você)\nTech Lead & SRE\ngithub.com/magnomct")
        row.cell("Arquiteto Carlos Vance\nTech Lead, SRE/DevOps, IA & Python Core")
        row.cell("1. Motor LangGraph (mediflow_agent.py) e Pydantic v2.\n2. Pipeline CI/CD GitHub Actions e métricas SRE.\n3. Governança, README trilíngue, memory.md e resiliência.")

        row = table.row()
        row.cell("Fernando Szekut\nFrontend & Workflows\ngithub.com/FSzekut")
        row.cell("Fernando Nexus\nIntegração de Agentes, Frontend/UX & Webhooks")
        row.cell("1. Design interativo Streamlit (visualizador de laudos).\n2. Webhooks de Notificação de Plantão Médico em tempo real.\n3. Pipeline multimodal para laudos/receitas escaneadas.")

        row = table.row()
        row.cell("Helder\nDados & Cloud OCI")
        row.cell("Atlas Data\nBanco de Dados, Persistência OCI Always Free")
        row.cell("1. oci_storage.py com segregação de pastas no bucket.\n2. Modelagem relacional/JSON de histórico clínico.\n3. Compliance estrito com a camada Always Free.")

        row = table.row()
        row.cell("Alessandro\nBackend & QA")
        row.cell("Marcus Builder\nBackend FastAPI, Módulo HitL & QA")
        row.cell("1. Endpoints REST FastAPI (app.py) /triagem e /auditoria.\n2. Gestão do Kanban GitHub Projects (setup_github_kanban.sh).\n3. Homologação dos 3 cenários e Vídeo Demo no YouTube.")

    # =========================================================================
    # PÁGINA 3: CRONOGRAMA DE 6 SEMANAS
    # =========================================================================
    pdf.add_page()
    pdf.chapter_title("3. Cronograma do Projeto — 6 Semanas (Dias Úteis: Segunda a Sexta)")

    col_crono = [24, 28, 42, 66, 20]
    with pdf.table(
        col_widths=col_crono,
        borders_layout="SINGLE_TOP_LINE",
        headings_style=FontFace(color=(255, 255, 255), fill_color=(30, 41, 59), emphasis="BOLD"),
        line_height=4.6,
    ) as table:
        row = table.row()
        row.cell("Semana")
        row.cell("Milestone")
        row.cell("Foco Principal")
        row.cell("Responsáveis e Entregáveis")
        row.cell("Status")

        row = table.row()
        row.cell("Semana 1\n(12-16/10)")
        row.cell("M1: Concepção &\nCore Spec")
        row.cell("Análise de medflow.md, ADRs e especificação base.")
        row.cell("• Carlos: Core Spec v0.1 e README trilíngue.\n• Helder: Setup OCI Always Free e WSL.\n• Alessandro & Fernando: Estrutura Git e LICENSE.")
        row.cell("[OK]\nConcluído")

        row = table.row()
        row.cell("Semana 2\n(19-23/10)")
        row.cell("M2: Modelagem &\nMotor LLM")
        row.cell("Schemas Pydantic, motor multimodal e OCI Storage.")
        row.cell("• Carlos: mediflow_schemas.py, NVIDIA NIM e SRE.\n• Fernando: Ingestão de imagens e protótipo UX.\n• Helder: Bucket OCI mediflow-documentos-clinicos.\n• Alessandro: Kanban GitHub e catálogo de testes.")
        row.cell("[OK]\nConcluído")

        row = table.row()
        row.cell("Semana 3\n(26-30/10)")
        row.cell("M3: Grafo Condicional\n& Workflows")
        row.cell("Nós do StateGraph, rotas de Emergência, Rotina, HitL.")
        row.cell("• Carlos: Grafo LangGraph week3/agent.py e SRE.\n• Fernando: Webhooks week3/notifications.py.\n• Helder: OCI Storage e SQLite week3/storage.py.\n• Alessandro: FastAPI week3/api.py e auto-testes.")
        row.cell("[EM CURSO]\nSemana 3")

        row = table.row()
        row.cell("Semana 4\n(02-06/11)")
        row.cell("M4: Banco OCI &\nCI/CD")
        row.cell("Segregação definitiva OCI, prontuário, CI/CD Actions.")
        row.cell("• Helder: Validação de uploads OCI remotos.\n• Carlos: GitHub Actions CI, métricas de latência SRE.\n• Fernando & Alessandro: Otimização da UI e dados.")
        row.cell("[PLANEJADO]\nSemana 4")

        row = table.row()
        row.cell("Semana 5\n(09-13/11)")
        row.cell("M5: Interface\nStreamlit & HitL")
        row.cell("Dashboard para auditor clínico e deploy na OCI.")
        row.cell("• Fernando & Alessandro: Painel Streamlit HitL e visualizador.\n• Carlos: Conexão agente-interface e testes de carga.\n• Helder: Deploy em VM OCI Compute Always Free.")
        row.cell("[PLANEJADO]\nSemana 5")

        row = table.row()
        row.cell("Semana 6\n(16-20/11)")
        row.cell("M6: Demonstração\n& Submissão")
        row.cell("Vídeo Demo no YouTube, validação final e submissão.")
        row.cell("• Alessandro & Fernando: Gravação e edição do Vídeo Demo.\n• Carlos: Revisão final de conformidade e código.\n• Helder: Auditoria final de custos zero na OCI.")
        row.cell("[PLANEJADO]\nSemana 6")

    # =========================================================================
    # PÁGINA 4: KANBAN GITHUB & ENTREGÁVEIS OFICIAIS DO HACKATHON
    # =========================================================================
    pdf.add_page()
    pdf.chapter_title("4. Modelo Kanban no GitHub Projects (Labels & Prioridades)")

    pdf.body_text(
        "O quadro do projeto no GitHub Projects utiliza automação via GitHub CLI (setup_github_kanban.sh) "
        "com a seguinte padronização de labels e responsabilidades:"
    )
    pdf.body_text(
        "• persona:carlos-sre-ia (#0052CC) — Carlos Magno: Tech Lead, SRE/DevOps, Arquitetura IA & Python Core\n"
        "• persona:fernando-nexus (#008080) — Fernando Szekut: Integração de Agentes, Frontend/UX & Workflows\n"
        "• persona:helder-data-oci (#D93F0B) — Helder: Especialista em Banco de Dados, Persistência OCI Always Free\n"
        "• persona:alessandro-app (#5319E7) — Alessandro: Desenvolvedor Backend FastAPI, Módulo HitL & QA\n"
        "• priority:critical-mvp (#FBCA04) — Requisitos obrigatórios do Checklist de Avaliação ONE G10\n"
        "• priority:differential (#0E8A16) — Recursos de destaque (Painel Streamlit HitL, Webhooks, Deploy OCI Compute)"
    )

    pdf.chapter_title("5. Entregáveis Oficiais do Hackathon ONE G10 (Tarefas 1 a 4)")

    pdf.section_title("[TAREFA 1] Documentação do Projeto (Formato Markdown)")
    pdf.body_text(
        "O MediFlow é um agente autônomo e inteligente para triagem, extração de entidades e roteamento "
        "condicional de documentos clínicos heterogêneos (laudos, receitas e guias TISS), desenvolvido "
        "pelo Equipo 22 com LangGraph, NVIDIA NIM (Llama 3.2 11B Vision), Google Gemini, Pydantic v2 e "
        "persistência segregada no Oracle Cloud Infrastructure (OCI) Object Storage (Camada Always Free)."
    )
    pdf.body_text(
        "• Equipe Oficial:\n"
        "  1. Carlos Magno — Tech Lead & Líder SRE/DevOps (github.com/magnomct)\n"
        "  2. Fernando Szekut — Integração de Agentes & Frontend/UX (github.com/FSzekut)\n"
        "  3. Helder — Especialista em Banco de Dados & OCI Always Free\n"
        "  4. Alessandro — Desenvolvedor Backend FastAPI & QA"
    )

    pdf.section_title("[TAREFA 2] Vídeo Demo do Projeto (Link do YouTube)")
    pdf.body_text(
        "• URL de Submissão: https://www.youtube.com/watch?v=MEDIFLOW_EQUIPO22_DEMO (Semana 6)\n"
        "• Roteiro de 3 Minutos: Apresentação do desafio clínico (Alessandro); Demonstração do motor LangGraph "
        "com IA da NVIDIA nos cenários de Rotina e Urgência TEP com alertas SRE (Carlos); Demonstração do visualizador "
        "multimodal e webhooks (Fernando); Fila de Human-in-the-Loop no Streamlit com aprovação em 1 clique (Alessandro & Fernando); "
        "e Exibição do bucket OCI Always Free com custo zero auditado (Helder)."
    )

    pdf.section_title("[TAREFA 3] Ferramentas da Equipe")
    pdf.body_text(
        "• Linguagem & Frameworks: Python 3.12+, LangGraph, Pydantic v2, FastAPI e Streamlit.\n"
        "• Modelos de IA: NVIDIA NIM (meta/llama-3.2-11b-vision-instruct) e Google Gemini 2.0 Flash.\n"
        "• Cloud & Dados: OCI Object Storage Always Free, OCI Autonomous Database (ATP), OCI Python SDK.\n"
        "• DevOps & SRE: WSL2 Ubuntu 24.04, GitHub Actions CI, Pytest, Webhooks e Netlify."
    )

    pdf.section_title("[TAREFA 4] Links Oficiais do Repositório")
    pdf.body_text(
        "• Repositório Git: https://github.com/ONE-G10-Brasil/G10-BRASIL-equipo-22-Medflow\n"
        "• Documentação Trilíngue: https://github.com/ONE-G10-Brasil/G10-BRASIL-equipo-22-Medflow/blob/main/README.md\n"
        "• Kanban do Projeto: https://github.com/ONE-G10-Brasil/G10-BRASIL-equipo-22-Medflow/projects\n"
        "• Bucket OCI Object Storage: oci://mediflow-documentos-clinicos@<tenancy-namespace>"
    )

    # Saída do arquivo PDF
    output_pdf = "/home/magno/ONE/PLANO_PROJETO_MEDIFLOW_HACKATHON.pdf"
    pdf.output(output_pdf)
    print(f"✅ PDF executivo gerado com sucesso em: {output_pdf}")


if __name__ == "__main__":
    generate_pdf()

