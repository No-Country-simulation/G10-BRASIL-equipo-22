"""Os 25 casos sintéticos: o conteúdo de cada documento e a saída esperada.

Tudo é fictício: pacientes, médicos, números de CRM, instituições, operadora, carteiras e
códigos de procedimento. Os CRMs não devem ser validados no cadastro do CFM.
"""
from modelo import (AUTORIZACOES, EMERGENCIA, FARMACIA, PRONTUARIO, REVISAO, Caso, Doc,
                    Guia, gabarito)

# --- Instituições -------------------------------------------------------------------------
HORIZONTE = ("Clínica Médica Horizonte", "Rua das Acácias, 1200 - Curitiba/PR - Tel. (41) 3000-0000")
VITALIS = ("Laboratório Vitalis Análises Clínicas",
           "Av. Sete de Setembro, 4000 - Curitiba/PR - Responsável técnica: Dra. Patrícia Moura Cavalcanti - CRM-PR 33908")
SERRA_VERDE = ("Centro de Diagnóstico por Imagem Serra Verde", "Rua XV de Novembro, 2100 - Curitiba/PR")
AURORA = ("Hospital Aurora do Vale", "Rua Brigadeiro Franco, 3100 - Curitiba/PR - Tel. (41) 3000-0100")
AURORA_RX = ("Hospital Aurora do Vale - Serviço de Radiologia", AURORA[1])
AURORA_LAB = ("Hospital Aurora do Vale - Laboratório de Análises Clínicas",
              "Rua Brigadeiro Franco, 3100 - Curitiba/PR - Responsável técnica: Dra. Simone Carvalho Weber - CRM-PR 40377")
OPERADORA = "SAÚDE INTEGRAL PLANOS"
REGISTRO_ANS = "419999"

# --- Médicos: nome, CRM, UF, especialidade -------------------------------------------------
MARINA = ("Dra. Marina Albuquerque Teles", "38214", "PR", "Clínica Médica")
RAFAEL = ("Dr. Rafael Nogueira Prado", "41577", "PR", "Cardiologia")
LUISA = ("Dra. Luísa Fontana Ribeiro", "27309", "PR", "Radiologia e Diagnóstico por Imagem")
HENRIQUE = ("Dr. Henrique Bastos Lemos", "162443", "SP", "Ortopedia e Traumatologia")
PATRICIA = ("Dra. Patrícia Moura Cavalcanti", "33908", "PR", "Patologia Clínica")
SIMONE = ("Dra. Simone Carvalho Weber", "40377", "PR", "Patologia Clínica")
OTAVIO = ("Dr. Otávio Sampaio Reis", "45120", "PR", "Clínica Médica")
CAMILA = ("Dra. Camila Duarte Viana", "71655", "MG", "Medicina de Família e Comunidade")
FABIO = ("Dr. Fábio Teixeira Guimarães", "29874", "PR", "Pneumologia")
GUSTAVO = ("Dr. Gustavo Antunes Pacheco", "47302", "PR", "Medicina de Emergência")
DIEGO = ("Dr. Diego Hoffmann Leal", "50211", "PR", "Medicina de Família e Comunidade")
BEATRIZ = ("Dra. Beatriz Lacerda Fonseca", "36752", "PR", "Reumatologia")
MAURO = ("Dr. Mauro Kenji Watanabe", "39981", "PR", "Ortopedia e Traumatologia")
SILVIO = ("Dr. Sílvio Ramos Bittencourt", "44610", "PR", "Clínica Médica")
REGINA = ("Dra. Regina Kfouri Matos", "42288", "PR", "Clínica Médica")
LEONARDO = ("Dr. Leonardo Vieira Campos", "", "PR", "Gastroenterologia")


def crm(m):
    """CRM no formato do contrato do README: "145892-SP"."""
    return f"{m[1]}-{m[2]}"


def linha_crm(m):
    return f"CRM-{m[2]} {m[1]}"


def assinatura(m):
    return [m[0], f"{m[3]} - {linha_crm(m)}"]


def solicitante(m):
    return f"{m[0]} - {linha_crm(m)}"


TABELA_LAB = ["Exame", "Resultado", "Unidade", "Valores de referência"]

CASOS: list[Caso] = []

# ============================== ROTINA ======================================================

CASOS.append(Caso(
    id="SINT-001", cenario="rotina", formato="pdf_digital", degradacao="nenhuma",
    canal_origem="Ambulatorio",
    documento=Doc(
        *HORIZONTE, titulo="RECEITUÁRIO", tamanho="A5",
        campos=[("Paciente", "José Aparecido Ramos"), ("Idade", "63 anos"), ("Data", "05/10/2026")],
        blocos=[
            ("secao", "Uso oral - uso contínuo"),
            ("med", "Losartana potássica 50 mg", "60 comprimidos", "Tomar 1 comprimido de 12 em 12 horas."),
            ("med", "Hidroclorotiazida 25 mg", "30 comprimidos", "Tomar 1 comprimido pela manhã."),
            ("med", "Besilato de anlodipino 5 mg", "30 comprimidos", "Tomar 1 comprimido ao dia."),
        ],
        assinatura=assinatura(RAFAEL), local_data="Curitiba, 5 de outubro de 2026"),
    esperado=gabarito(
        tipo="Receituário Médico", especialidade="Cardiologia", prioridade="Rotina",
        paciente="José Aparecido Ramos", idade=63, medico=RAFAEL[0], crm=crm(RAFAEL),
        medicamentos=[
            ("Losartana potássica", "50 mg", "oral", "1 comprimido de 12 em 12 horas"),
            ("Hidroclorotiazida", "25 mg", "oral", "1 comprimido pela manhã"),
            ("Besilato de anlodipino", "5 mg", "oral", "1 comprimido ao dia"),
        ],
        destino=FARMACIA),
    cid_aceitos=[None, "I10"],
    motivo="Receita legível e completa, doses habituais, paciente e CRM identificados."))

CASOS.append(Caso(
    id="SINT-002", cenario="rotina", formato="texto", degradacao="nenhuma",
    canal_origem="Ambulatorio",
    documento=Doc(
        "Unidade Básica de Saúde Vila Esperança", "Rua Itaúna, 450 - Belo Horizonte/MG",
        titulo="RECEITUÁRIO SIMPLES", tamanho="A5",
        campos=[("Paciente", "Ana Beatriz Kowalski"), ("Idade", "34 anos"), ("Data", "08/10/2026")],
        blocos=[
            ("secao", "Uso oral"),
            ("med", "Amoxicilina 500 mg cápsula", "21 cápsulas", "Tomar 1 cápsula de 8 em 8 horas por 7 dias."),
            ("med", "Dipirona monoidratada 500 mg comprimido", "10 comprimidos",
             "Tomar 1 comprimido de 6 em 6 horas se dor ou febre."),
            ("par", "Diagnóstico: sinusite aguda (CID-10 J01.9)."),
        ],
        assinatura=assinatura(CAMILA), local_data="Belo Horizonte, 8 de outubro de 2026"),
    esperado=gabarito(
        tipo="Receituário Médico", especialidade="Medicina de Família e Comunidade", prioridade="Rotina",
        paciente="Ana Beatriz Kowalski", idade=34, medico=CAMILA[0], crm=crm(CAMILA),
        diagnostico="Sinusite aguda", cid="J01.9",
        medicamentos=[
            ("Amoxicilina", "500 mg", "oral", "1 cápsula de 8 em 8 horas por 7 dias"),
            ("Dipirona monoidratada", "500 mg", "oral", "1 comprimido de 6 em 6 horas se dor ou febre"),
        ],
        destino=FARMACIA),
    cid_aceitos=["J01.9", "J01"],
    motivo="Receita completa com diagnóstico e CID escritos."))

CASOS.append(Caso(
    id="SINT-003", cenario="rotina", formato="pdf_digital", degradacao="nenhuma",
    canal_origem="Laboratorio",
    documento=Doc(
        *VITALIS, titulo="LAUDO DE EXAMES LABORATORIAIS",
        campos=[("Paciente", "Marcos Vinícius Ferreira"), ("Idade", "45 anos"), ("Sexo", "Masculino"),
                ("Atendimento", "2026-100734"), ("Solicitante", solicitante(MARINA)),
                ("Data da coleta", "07/10/2026")],
        blocos=[
            ("secao", "Hemograma completo"),
            ("par", "Material: sangue total (EDTA). Método: citometria de fluxo automatizada."),
            ("tabela", TABELA_LAB, [
                ("Hemácias", "5,02", "milhões/mm³", "4,50 a 5,90"),
                ("Hemoglobina", "15,1", "g/dL", "13,5 a 17,5"),
                ("Hematócrito", "44,8", "%", "41,0 a 53,0"),
                ("VCM", "89,2", "fL", "80,0 a 100,0"),
                ("HCM", "30,1", "pg", "26,0 a 34,0"),
                ("CHCM", "33,7", "g/dL", "31,0 a 36,0"),
                ("RDW", "12,9", "%", "11,5 a 14,5"),
                ("Leucócitos", "6.800", "/mm³", "4.000 a 11.000"),
                ("Neutrófilos", "58", "%", "40 a 75"),
                ("Linfócitos", "31", "%", "20 a 45"),
                ("Monócitos", "7", "%", "2 a 10"),
                ("Eosinófilos", "3", "%", "1 a 6"),
                ("Basófilos", "1", "%", "0 a 2"),
                ("Plaquetas", "245.000", "/mm³", "150.000 a 450.000"),
            ]),
            ("par", "Liberado em 07/10/2026 às 16h42."),
        ],
        assinatura=assinatura(PATRICIA)),
    esperado=gabarito(
        tipo="Laudo de Exame Laboratorial", especialidade="Patologia Clínica", prioridade="Rotina",
        paciente="Marcos Vinícius Ferreira", idade=45, medico=MARINA[0], crm=crm(MARINA),
        exame="Hemograma completo", destino=PRONTUARIO),
    cid_aceitos=[None, "Z00.0"],
    armadilha="Duas médicas no laudo: a solicitante (Dra. Marina) e a responsável técnica que assina "
              "(Dra. Patrícia). medico_solicitante é a Dra. Marina.",
    motivo="Hemograma normal, completo e identificado."))

CASOS.append(Caso(
    id="SINT-004", cenario="rotina", formato="pdf_escaneado", degradacao="scan_leve",
    canal_origem="Laboratorio",
    documento=Doc(
        *VITALIS, titulo="LAUDO DE EXAMES LABORATORIAIS",
        campos=[("Paciente", "Sueli Aparecida Nunes"), ("Idade", "58 anos"), ("Sexo", "Feminino"),
                ("Atendimento", "2026-101187"), ("Solicitante", solicitante(DIEGO)),
                ("Data da coleta", "09/10/2026"),
                ("Informação clínica", "Diabetes mellitus tipo 2 em acompanhamento")],
        blocos=[
            ("secao", "Bioquímica"),
            ("tabela", TABELA_LAB, [
                ("Glicose em jejum", "142", "mg/dL", "70 a 99"),
                ("Hemoglobina glicada (HbA1c)", "7,4", "%", "Normal: abaixo de 5,7"),
                ("Creatinina", "0,9", "mg/dL", "0,6 a 1,1"),
                ("Colesterol total", "198", "mg/dL", "Desejável: abaixo de 190"),
                ("LDL-colesterol", "112", "mg/dL", "Meta conforme risco cardiovascular"),
                ("HDL-colesterol", "46", "mg/dL", "Acima de 40"),
                ("Triglicerídeos", "168", "mg/dL", "Desejável: abaixo de 150"),
            ]),
            ("par", "Valores fora da faixa de referência devem ser interpretados pelo médico assistente."),
        ],
        assinatura=assinatura(PATRICIA)),
    esperado=gabarito(
        tipo="Laudo de Exame Laboratorial", especialidade="Patologia Clínica", prioridade="Rotina",
        paciente="Sueli Aparecida Nunes", idade=58, medico=DIEGO[0], crm=crm(DIEGO),
        exame="Glicose em jejum, hemoglobina glicada, creatinina e perfil lipídico",
        diagnostico="Diabetes mellitus tipo 2", cid="E11.9", destino=PRONTUARIO),
    cid_aceitos=["E11.9", "E11", None],
    armadilha="Valores alterados, mas nenhum crítico: alterado não é urgente.",
    motivo="Controle de diabetes com resultados fora da referência e sem valor crítico."))

CASOS.append(Caso(
    id="SINT-005", cenario="rotina", formato="texto", degradacao="nenhuma",
    canal_origem="Ambulatorio",
    documento=Doc(
        *SERRA_VERDE, titulo="LAUDO DE RADIOGRAFIA",
        campos=[("Paciente", "Gabriel Henrique Lopes"), ("Idade", "29 anos"),
                ("Solicitante", solicitante(FABIO)), ("Data do exame", "10/10/2026")],
        blocos=[
            ("secao", "Radiografia de tórax (PA e perfil)"),
            ("par", "Indicação clínica: tosse seca há 10 dias, sem febre."),
            ("secao", "Achados"),
            ("par", "Campos pulmonares sem opacidades. Seios costofrênicos livres. Área cardíaca dentro "
                    "dos limites da normalidade. Mediastino centrado. Estruturas ósseas preservadas."),
            ("secao", "Conclusão"),
            ("par", "Radiografia de tórax sem alterações."),
        ],
        assinatura=assinatura(LUISA)),
    esperado=gabarito(
        tipo="Laudo de Exame de Imagem", especialidade="Radiologia", prioridade="Rotina",
        paciente="Gabriel Henrique Lopes", idade=29, medico=FABIO[0], crm=crm(FABIO),
        exame="Radiografia de tórax PA e perfil", destino=PRONTUARIO),
    cid_aceitos=[None, "R05"],
    motivo="Exame normal, completo e identificado."))

CASOS.append(Caso(
    id="SINT-006", cenario="rotina", formato="pdf_digital", degradacao="nenhuma",
    canal_origem="Central_Autorizacoes",
    documento=Guia(
        operadora=OPERADORA, registro_ans=REGISTRO_ANS, numero_guia="2026-0008812",
        carteira="0 8812 004517 22 9", beneficiario="Rosângela Maria Pires",
        contratado="Clínica Ortopédica Movimento", profissional=HENRIQUE[0], conselho="CRM",
        numero_conselho=HENRIQUE[1], uf=HENRIQUE[2], cbo="225270", carater="1 - Eletiva",
        data_solicitacao="09/10/2026",
        indicacao_clinica="Dor no joelho direito há 3 meses, com episódios de bloqueio articular. "
                          "Suspeita de lesão meniscal.",
        procedimentos=[("22", "99000117", "Ressonância magnética de joelho direito", "1")]),
    esperado=gabarito(
        tipo="Guia de Solicitação de Procedimento", especialidade="Ortopedia", prioridade="Rotina",
        paciente="Rosângela Maria Pires", idade=None, medico=HENRIQUE[0], crm=crm(HENRIQUE),
        exames_solicitados=["Ressonância magnética de joelho direito"],
        diagnostico="Suspeita de lesão meniscal no joelho direito", cid="M23.2",
        destino=AUTORIZACOES),
    cid_aceitos=["M23.2", "M23.3", "S83.2", "M25.5", None],
    motivo="Pedido eletivo completo: vai para a auditoria de autorizações sem revisão extra."))

CASOS.append(Caso(
    id="SINT-007", cenario="rotina", formato="pdf_digital", degradacao="nenhuma",
    canal_origem="Internacao",
    documento=Doc(
        *AURORA, titulo="RELATÓRIO DE ALTA HOSPITALAR",
        campos=[("Paciente", "Antônio Carlos Wisniewski"), ("Idade", "72 anos"),
                ("Prontuário", "0048213"), ("Unidade", "Clínica Médica - 3º andar"),
                ("Internação", "01/10/2026"), ("Alta", "06/10/2026")],
        blocos=[
            ("secao", "Diagnóstico principal"),
            ("par", "Pneumonia adquirida na comunidade (CID-10 J18.9)."),
            ("secao", "Comorbidades"),
            ("par", "Doença pulmonar obstrutiva crônica (J44.9); hipertensão arterial sistêmica (I10)."),
            ("secao", "Resumo da internação"),
            ("par", "Paciente admitido pelo pronto-socorro com febre (38,6 °C), tosse produtiva e dispneia, "
                    "com saturação de oxigênio de 91% em ar ambiente. Radiografia de tórax com consolidação "
                    "em lobo inferior direito. Recebeu ceftriaxona e azitromicina por via endovenosa, com boa "
                    "resposta clínica, e passou para antibiótico oral no 4º dia."),
            ("secao", "Condições de alta"),
            ("par", "Alta em bom estado geral, afebril há 72 horas, eupneico, saturação de 95% em ar ambiente."),
            ("secao", "Prescrição de alta"),
            ("med", "Amoxicilina + clavulanato de potássio 875 mg + 125 mg", "6 comprimidos",
             "Tomar 1 comprimido de 12 em 12 horas por mais 3 dias."),
            ("par", "Manter as medicações de uso contínuo já prescritas."),
            ("secao", "Orientações"),
            ("par", "Retorno ao ambulatório de clínica médica em 15 dias, com radiografia de tórax de controle. "
                    "Procurar o pronto-socorro em caso de febre, piora da falta de ar ou dor no peito."),
        ],
        assinatura=assinatura(OTAVIO), local_data="Curitiba, 6 de outubro de 2026"),
    esperado=gabarito(
        tipo="Relatório de Alta", especialidade="Clínica Médica", prioridade="Rotina",
        paciente="Antônio Carlos Wisniewski", idade=72, medico=OTAVIO[0], crm=crm(OTAVIO),
        exames_solicitados=["Radiografia de tórax de controle"],
        diagnostico="Pneumonia adquirida na comunidade", cid="J18.9",
        medicamentos=[("Amoxicilina + clavulanato de potássio", "875 mg + 125 mg", "oral",
                       "1 comprimido de 12 em 12 horas por 3 dias")],
        destino=PRONTUARIO),
    cid_aceitos=["J18.9", "J18"],
    armadilha="O resumo cita febre, dispneia e saturação de 91% na admissão; na alta o paciente está "
              "estável. Sintoma passado não é urgência.",
    motivo="Alta de rotina, paciente estável."))

CASOS.append(Caso(
    id="SINT-008", cenario="rotina", formato="imagem", degradacao="foto",
    canal_origem="Ambulatorio",
    documento=Doc(
        "Policlínica Monte Claro", "Rua Chile, 1500 - Curitiba/PR", titulo="ATESTADO MÉDICO",
        tamanho="A5", campos=[],
        blocos=[
            ("par", "Atesto, para os devidos fins, que a Sra. Juliana Santos Moreira esteve sob meus "
                    "cuidados profissionais nesta data e necessita de 3 (três) dias de afastamento de suas "
                    "atividades laborais, a partir de 13/10/2026, por motivo de doença."),
            ("par", "CID-10: J11 (informado com autorização da paciente)."),
        ],
        assinatura=assinatura(MARINA), local_data="Curitiba, 13 de outubro de 2026"),
    esperado=gabarito(
        tipo="Atestado Médico", especialidade="Clínica Médica", prioridade="Rotina",
        paciente="Juliana Santos Moreira", idade=None, medico=MARINA[0], crm=crm(MARINA),
        diagnostico="Influenza (gripe)", cid="J11", destino=PRONTUARIO,
        extras={"dias_afastamento": 3}),
    cid_aceitos=["J11", "J11.1", "J11.8"],
    motivo="Atestado completo, fotografado com celular."))

CASOS.append(Caso(
    id="SINT-009", cenario="rotina", formato="imagem", degradacao="scan_leve",
    canal_origem="Ambulatorio",
    documento=Doc(
        "Unidade de Saúde Boa Vista", "Av. Paraná, 2600 - Curitiba/PR", titulo="RECEITUÁRIO", tamanho="A5",
        campos=[("Paciente", "Benedito Alves Correia"), ("Idade", "67 anos"), ("Data", "14/10/2026")],
        blocos=[
            ("secao", "Uso oral - uso contínuo"),
            ("med", "Cloridrato de metformina 850 mg", "60 comprimidos",
             "Tomar 1 comprimido após o café da manhã e 1 após o jantar."),
            ("med", "Sinvastatina 20 mg", "30 comprimidos", "Tomar 1 comprimido à noite."),
            ("med", "Ácido acetilsalicílico 100 mg", "30 comprimidos", "Tomar 1 comprimido após o almoço."),
        ],
        assinatura=assinatura(DIEGO), local_data="Curitiba, 14 de outubro de 2026"),
    esperado=gabarito(
        tipo="Receituário Médico", especialidade="Medicina de Família e Comunidade", prioridade="Rotina",
        paciente="Benedito Alves Correia", idade=67, medico=DIEGO[0], crm=crm(DIEGO),
        medicamentos=[
            ("Cloridrato de metformina", "850 mg", "oral", "1 comprimido após o café da manhã e 1 após o jantar"),
            ("Sinvastatina", "20 mg", "oral", "1 comprimido à noite"),
            ("Ácido acetilsalicílico", "100 mg", "oral", "1 comprimido após o almoço"),
        ],
        destino=FARMACIA),
    cid_aceitos=[None, "E11.9", "E11"],
    motivo="Receita de uso contínuo, digitalizada e legível."))

CASOS.append(Caso(
    id="SINT-010", cenario="rotina", formato="imagem", degradacao="foto",
    canal_origem="Ambulatorio",
    documento=Doc(
        FABIO[0], f"Pneumologia - {linha_crm(FABIO)} - Rua Comendador Araújo, 500, sala 12 - Curitiba/PR",
        titulo="", tamanho="A5", manuscrito=True, letra="legivel",
        campos=[("Paciente", "Lúcia Helena Prates"), ("Idade", "55 anos")],
        blocos=[
            ("linha", "Uso inalatório:"),
            ("linha", "1) Budesonida + formoterol 200/6 mcg (cápsula inalatória)"),
            ("linha", "     inalar 1 cápsula de 12/12h - uso contínuo"),
            ("linha", "2) Salbutamol 100 mcg spray"),
            ("linha", "     2 jatos se falta de ar, até de 6/6h"),
        ],
        assinatura=[], local_data="Curitiba, 14/10/2026",
        carimbo=[FABIO[0], FABIO[3], linha_crm(FABIO)]),
    esperado=gabarito(
        tipo="Receituário Médico", especialidade="Pneumologia", prioridade="Rotina",
        paciente="Lúcia Helena Prates", idade=55, medico=FABIO[0], crm=crm(FABIO),
        medicamentos=[
            ("Budesonida + formoterol", "200/6 mcg", "inalatória", "1 cápsula de 12 em 12 horas, uso contínuo"),
            ("Salbutamol", "100 mcg", "inalatória", "2 jatos se falta de ar, até de 6 em 6 horas"),
        ],
        destino=FARMACIA),
    cid_aceitos=[None, "J45.9", "J44.9"],
    motivo="Receita manuscrita, mas legível e completa.",
    armadilha="Escrita à mão e fotografada: testa a leitura multimodal num caso que deve passar direto."))

# ============================== URGÊNCIA ====================================================

CASOS.append(Caso(
    id="SINT-011", cenario="urgencia", formato="texto", degradacao="nenhuma",
    canal_origem="Pronto_Socorro",
    documento=Doc(
        *AURORA_RX, titulo="LAUDO DE TOMOGRAFIA COMPUTADORIZADA",
        campos=[("Paciente", "Larissa Prado Mendonça"), ("Idade", "41 anos"),
                ("Atendimento", "2026-PS-08790"), ("Solicitante", solicitante(OTAVIO)),
                ("Data do exame", "15/10/2026")],
        blocos=[
            ("secao", "Angiotomografia de tórax (protocolo para tromboembolismo pulmonar)"),
            ("par", "Indicação clínica: dispneia súbita e dor torácica ventilatório-dependente; "
                    "pós-operatório de colecistectomia há 10 dias."),
            ("secao", "Achados"),
            ("par", "Falhas de enchimento nas artérias pulmonares lobares inferiores bilaterais e em ramos "
                    "segmentares do lobo médio. Relação entre os diâmetros dos ventrículos direito e esquerdo "
                    "de 1,2, sugestiva de sobrecarga das câmaras direitas. Pequeno derrame pleural à direita."),
            ("secao", "Impressão diagnóstica"),
            ("par", "Tromboembolismo pulmonar agudo bilateral, com sinais de sobrecarga ventricular direita."),
            ("par", "Resultado crítico comunicado ao médico assistente às 14h20."),
        ],
        assinatura=assinatura(LUISA)),
    esperado=gabarito(
        tipo="Laudo de Exame de Imagem", especialidade="Radiologia / Pneumologia", prioridade="Urgente",
        paciente="Larissa Prado Mendonça", idade=41, medico=OTAVIO[0], crm=crm(OTAVIO),
        exame="Angiotomografia de tórax", diagnostico="Tromboembolismo pulmonar agudo bilateral",
        cid="I26.0", destino=EMERGENCIA, alerta=True),
    cid_aceitos=["I26.0", "I26.9"],
    armadilha="A médica que assina é a radiologista; o solicitante é o Dr. Otávio.",
    motivo="TEP agudo com sobrecarga de ventrículo direito: achado crítico."))

CASOS.append(Caso(
    id="SINT-012", cenario="urgencia", formato="pdf_digital", degradacao="nenhuma",
    canal_origem="Pronto_Socorro",
    documento=Doc(
        *AURORA_RX, titulo="LAUDO DE TOMOGRAFIA COMPUTADORIZADA",
        campos=[("Paciente", "Sebastião Rodrigues Filho"), ("Idade", "74 anos"),
                ("Atendimento", "2026-PS-08802"), ("Solicitante", solicitante(GUSTAVO)),
                ("Data do exame", "16/10/2026")],
        blocos=[
            ("secao", "Tomografia computadorizada de crânio sem contraste"),
            ("par", "Indicação clínica: rebaixamento do nível de consciência e fraqueza no lado esquerdo do "
                    "corpo, de início súbito há cerca de 2 horas."),
            ("secao", "Achados"),
            ("par", "Hematoma intraparenquimatoso na região nucleocapsular direita, medindo cerca de "
                    "4,1 x 3,2 cm (volume estimado de 26 mL), com edema ao redor e efeito de massa, "
                    "determinando desvio da linha média de 6 mm para a esquerda. Sem sinais de inundação "
                    "ventricular. Demais estruturas sem alterações agudas."),
            ("secao", "Impressão diagnóstica"),
            ("par", "Hemorragia intraparenquimatosa aguda nucleocapsular direita, com efeito de massa."),
            ("par", "Achado crítico comunicado à equipe do pronto-socorro às 22h05."),
        ],
        assinatura=assinatura(LUISA)),
    esperado=gabarito(
        tipo="Laudo de Exame de Imagem", especialidade="Radiologia / Neurologia", prioridade="Urgente",
        paciente="Sebastião Rodrigues Filho", idade=74, medico=GUSTAVO[0], crm=crm(GUSTAVO),
        exame="Tomografia computadorizada de crânio sem contraste",
        diagnostico="Hemorragia intraparenquimatosa aguda", cid="I61.0",
        destino=EMERGENCIA, alerta=True),
    cid_aceitos=["I61.0", "I61.9", "I61"],
    motivo="AVC hemorrágico com desvio da linha média: achado crítico."))

CASOS.append(Caso(
    id="SINT-013", cenario="urgencia", formato="pdf_escaneado", degradacao="scan_leve",
    canal_origem="Laboratorio",
    documento=Doc(
        *VITALIS, titulo="LAUDO DE EXAMES LABORATORIAIS",
        campos=[("Paciente", "Iracema Batista Souza"), ("Idade", "68 anos"), ("Sexo", "Feminino"),
                ("Atendimento", "2026-101402"), ("Solicitante", solicitante(DIEGO)),
                ("Data da coleta", "16/10/2026")],
        blocos=[
            ("secao", "Bioquímica"),
            ("tabela", TABELA_LAB, [
                ("Potássio", "6,9", "mEq/L", "3,5 a 5,1"),
                ("Sódio", "136", "mEq/L", "136 a 145"),
                ("Ureia", "118", "mg/dL", "15 a 45"),
                ("Creatinina", "3,8", "mg/dL", "0,6 a 1,1"),
            ]),
            ("destaque", "VALOR CRÍTICO: potássio 6,9 mEq/L. Resultado confirmado em segunda dosagem e "
                         "comunicado por telefone à unidade solicitante em 16/10/2026, às 09h12."),
        ],
        assinatura=assinatura(PATRICIA)),
    esperado=gabarito(
        tipo="Laudo de Exame Laboratorial", especialidade="Patologia Clínica", prioridade="Urgente",
        paciente="Iracema Batista Souza", idade=68, medico=DIEGO[0], crm=crm(DIEGO),
        exame="Potássio, sódio, ureia e creatinina", destino=EMERGENCIA, alerta=True),
    cid_aceitos=[None, "E87.5", "N17.9", "N18.9"],
    armadilha="Não há diagnóstico escrito: a urgência vem do valor crítico na tabela.",
    motivo="Potássio de 6,9 mEq/L: risco de arritmia grave."))

CASOS.append(Caso(
    id="SINT-014", cenario="urgencia", formato="imagem", degradacao="foto",
    canal_origem="Pronto_Socorro",
    documento=Doc(
        *AURORA_LAB, titulo="RESULTADO DE EXAME",
        campos=[("Paciente", "Paulo Roberto Zanella"), ("Idade", "59 anos"), ("Sexo", "Masculino"),
                ("Atendimento", "2026-PS-08815"), ("Solicitante", solicitante(GUSTAVO)),
                ("Coleta", "17/10/2026 às 03h05")],
        blocos=[
            ("secao", "Marcadores cardíacos"),
            ("tabela", TABELA_LAB, [
                ("Troponina I ultrassensível", "1.850", "ng/L", "Abaixo de 34 (homens)"),
                ("CK-MB massa", "38,0", "ng/mL", "Abaixo de 5,0"),
            ]),
            ("destaque", "RESULTADO CRÍTICO comunicado à equipe do pronto-socorro às 03h40."),
        ],
        assinatura=assinatura(SIMONE)),
    esperado=gabarito(
        tipo="Laudo de Exame Laboratorial", especialidade="Patologia Clínica / Cardiologia",
        prioridade="Urgente", paciente="Paulo Roberto Zanella", idade=59, medico=GUSTAVO[0],
        crm=crm(GUSTAVO), exame="Troponina I ultrassensível e CK-MB massa",
        destino=EMERGENCIA, alerta=True),
    cid_aceitos=[None, "I21.9", "I21.4", "I24.9"],
    armadilha="Fotografado com celular e sem diagnóstico escrito: a urgência vem da troponina.",
    motivo="Troponina mais de 50 vezes acima da referência: suspeita de infarto."))

CASOS.append(Caso(
    id="SINT-015", cenario="urgencia", formato="pdf_digital", degradacao="nenhuma",
    canal_origem="Pronto_Socorro",
    documento=Doc(
        *AURORA_RX, titulo="LAUDO DE RADIOGRAFIA",
        campos=[("Paciente", "Thiago Martins Ribeiro"), ("Idade", "22 anos"),
                ("Atendimento", "2026-PS-08821"), ("Solicitante", solicitante(OTAVIO)),
                ("Data do exame", "18/10/2026")],
        blocos=[
            ("secao", "Radiografia de tórax (AP, no leito)"),
            ("par", "Indicação clínica: dor torácica súbita à direita e falta de ar."),
            ("secao", "Achados"),
            ("par", "Pneumotórax volumoso à direita, com colapso quase completo do pulmão direito, desvio do "
                    "mediastino para a esquerda e rebaixamento da cúpula diafragmática direita."),
            ("secao", "Impressão diagnóstica"),
            ("par", "Pneumotórax hipertensivo à direita."),
            ("par", "Achado crítico comunicado ao médico assistente às 11h15."),
        ],
        assinatura=assinatura(LUISA)),
    esperado=gabarito(
        tipo="Laudo de Exame de Imagem", especialidade="Radiologia", prioridade="Urgente",
        paciente="Thiago Martins Ribeiro", idade=22, medico=OTAVIO[0], crm=crm(OTAVIO),
        exame="Radiografia de tórax AP no leito", diagnostico="Pneumotórax hipertensivo à direita",
        cid="J93.0", destino=EMERGENCIA, alerta=True),
    cid_aceitos=["J93.0", "J93.1", "J93.9"],
    motivo="Pneumotórax hipertensivo: emergência imediata."))

CASOS.append(Caso(
    id="SINT-016", cenario="urgencia", formato="pdf_escaneado", degradacao="scan_leve",
    canal_origem="Central_Autorizacoes",
    documento=Guia(
        operadora=OPERADORA, registro_ans=REGISTRO_ANS, numero_guia="2026-0009120",
        carteira="0 8812 019934 07 1", beneficiario="Cláudio Henrique Barbosa",
        contratado="Hospital Aurora do Vale", profissional=RAFAEL[0], conselho="CRM",
        numero_conselho=RAFAEL[1], uf=RAFAEL[2], cbo="225120", carater="2 - Urgência/Emergência",
        data_solicitacao="18/10/2026",
        indicacao_clinica="Dor torácica intensa, em rasgada, com irradiação para o dorso e assimetria de "
                          "pulsos nos membros superiores. Suspeita de dissecção aguda de aorta.",
        procedimentos=[("22", "99000452", "Angiotomografia de aorta torácica e abdominal", "1")]),
    esperado=gabarito(
        tipo="Guia de Solicitação de Procedimento", especialidade="Cardiologia", prioridade="Urgente",
        paciente="Cláudio Henrique Barbosa", idade=None, medico=RAFAEL[0], crm=crm(RAFAEL),
        exames_solicitados=["Angiotomografia de aorta torácica e abdominal"],
        diagnostico="Suspeita de dissecção aguda de aorta", cid="I71.0", destino=AUTORIZACOES),
    cid_aceitos=["I71.0"],
    decisao_pendente="Guia com caráter de urgência: aqui vai para a Auditoria de Autorizações com "
                     "prioridade Urgente (a autorização precisa sair na hora, mas quem decide é a operadora). "
                     "O grafo do README manda toda urgência para a fila de emergência. Decidir com a equipe.",
    motivo="Pedido urgente de exame para suspeita de dissecção de aorta."))

CASOS.append(Caso(
    id="SINT-017", cenario="urgencia", formato="texto", degradacao="nenhuma",
    canal_origem="Laboratorio",
    documento=Doc(
        *VITALIS, titulo="LAUDO DE EXAMES LABORATORIAIS",
        campos=[("Paciente", "Maria das Graças Silva"), ("Idade", "47 anos"), ("Sexo", "Feminino"),
                ("Atendimento", "2026-101655"), ("Solicitante", solicitante(MARINA)),
                ("Data da coleta", "19/10/2026")],
        blocos=[
            ("secao", "Hemograma"),
            ("tabela", TABELA_LAB, [
                ("Hemoglobina", "5,8", "g/dL", "12,0 a 15,5"),
                ("Hematócrito", "18,9", "%", "36,0 a 46,0"),
                ("VCM", "68,0", "fL", "80,0 a 100,0"),
                ("HCM", "20,5", "pg", "26,0 a 34,0"),
                ("Leucócitos", "7.200", "/mm³", "4.000 a 11.000"),
                ("Plaquetas", "412.000", "/mm³", "150.000 a 450.000"),
            ]),
            ("destaque", "VALOR CRÍTICO: hemoglobina 5,8 g/dL, confirmada em segunda amostra. Comunicado à "
                         "médica solicitante em 19/10/2026, às 10h30."),
            ("par", "Observação: microcitose e hipocromia acentuadas."),
        ],
        assinatura=assinatura(PATRICIA)),
    esperado=gabarito(
        tipo="Laudo de Exame Laboratorial", especialidade="Patologia Clínica", prioridade="Urgente",
        paciente="Maria das Graças Silva", idade=47, medico=MARINA[0], crm=crm(MARINA),
        exame="Hemograma", destino=EMERGENCIA, alerta=True),
    cid_aceitos=[None, "D64.9", "D50.9", "D50.0"],
    motivo="Hemoglobina de 5,8 g/dL: anemia grave."))

# ============================== AMBÍGUO =====================================================

CASOS.append(Caso(
    id="SINT-018", cenario="ambiguo", formato="imagem", degradacao="foto",
    canal_origem="Ambulatorio",
    documento=Doc(
        SILVIO[0], f"{SILVIO[3]} - {linha_crm(SILVIO)} - Rua Marechal Deodoro, 900, sala 3 - Curitiba/PR",
        titulo="", tamanho="A5", manuscrito=True, letra="ruim",
        campos=[("Paciente", "Edson Luiz Krüger"), ("Data", "20/10/2026")],
        blocos=[
            ("linha", "Uso oral"),
            ("linha", "1) Amitriptilina 25mg ------ 30 cp"),
            ("linha", "      1 cp à noite"),
            ("linha", "2) {{ILEGIVEL:11}} ------ 1 cx"),
            ("linha", "      1 cp 2x ao dia"),
        ],
        assinatura=[], local_data=""),
    esperado=gabarito(
        tipo="Receituário Médico", especialidade="Clínica Médica", prioridade="Rotina",
        paciente="Edson Luiz Krüger", idade=None, medico=SILVIO[0], crm=crm(SILVIO),
        medicamentos=[
            ("Amitriptilina", "25 mg", "oral", "1 comprimido à noite"),
            (None, None, "oral", "1 comprimido 2 vezes ao dia"),
        ],
        destino=REVISAO, auditoria=True),
    cid_aceitos=[None],
    campos_ausentes=["medicamentos[1].nome", "medicamentos[1].dosagem"],
    motivo="Nome do segundo medicamento ilegível e sem dosagem: a farmácia não pode dispensar sem confirmar."))

CASOS.append(Caso(
    id="SINT-019", cenario="ambiguo", formato="pdf_digital", degradacao="nenhuma",
    canal_origem="Ambulatorio",
    documento=Doc(
        f"{BEATRIZ[0]} - {BEATRIZ[3]}", "Rua Visconde de Guarapuava, 3000, sala 5 - Curitiba/PR",
        titulo="RECEITUÁRIO", tamanho="A5",
        campos=[("Paciente", "Neusa Terezinha Becker"), ("Idade", "64 anos"), ("Data", "20/10/2026")],
        blocos=[
            ("secao", "Uso oral"),
            ("med", "Metotrexato 2,5 mg", "60 comprimidos", "Tomar 4 comprimidos (10 mg) por dia."),
            ("med", "Ácido fólico 5 mg", "4 comprimidos",
             "Tomar 1 comprimido uma vez por semana, no dia seguinte ao metotrexato."),
            ("med", "Prednisona 5 mg", "30 comprimidos", "Tomar 1 comprimido pela manhã."),
            ("par", "Diagnóstico: artrite reumatoide (CID-10 M06.9)."),
        ],
        assinatura=assinatura(BEATRIZ), local_data="Curitiba, 20 de outubro de 2026"),
    esperado=gabarito(
        tipo="Receituário Médico", especialidade="Reumatologia", prioridade="Rotina",
        paciente="Neusa Terezinha Becker", idade=64, medico=BEATRIZ[0], crm=crm(BEATRIZ),
        diagnostico="Artrite reumatoide", cid="M06.9",
        medicamentos=[
            ("Metotrexato", "2,5 mg", "oral", "4 comprimidos (10 mg) por dia"),
            ("Ácido fólico", "5 mg", "oral", "1 comprimido uma vez por semana"),
            ("Prednisona", "5 mg", "oral", "1 comprimido pela manhã"),
        ],
        destino=REVISAO, auditoria=True),
    cid_aceitos=["M06.9", "M06"],
    armadilha="Documento legível e completo: o problema é clínico, não de leitura.",
    motivo="Metotrexato em dose diária: na artrite reumatoide o uso é semanal, e a dose diária pode ser "
           "fatal. Prescrição de alto risco, precisa de revisão antes de dispensar."))

CASOS.append(Caso(
    id="SINT-020", cenario="ambiguo", formato="texto", degradacao="nenhuma",
    canal_origem="Ambulatorio",
    documento=Doc(
        "Clínica Ortopédica Movimento", "Rua Vergueiro, 2400 - São Paulo/SP", titulo="RECEITUÁRIO",
        tamanho="A5",
        campos=[("Paciente", "Lucas Gabriel Teodoro"), ("Idade", "19 anos"), ("Data", "21/10/2026")],
        blocos=[
            ("secao", "Uso oral"),
            ("med", "Paracetamol 750 mg", "36 comprimidos", "Tomar 2 comprimidos de 4 em 4 horas, se dor."),
            ("med", "Cloridrato de ciclobenzaprina 5 mg", "5 comprimidos",
             "Tomar 1 comprimido à noite por 5 dias."),
            ("par", "Diagnóstico: lombalgia aguda (CID-10 M54.5)."),
        ],
        assinatura=assinatura(HENRIQUE), local_data="São Paulo, 21 de outubro de 2026"),
    esperado=gabarito(
        tipo="Receituário Médico", especialidade="Ortopedia", prioridade="Rotina",
        paciente="Lucas Gabriel Teodoro", idade=19, medico=HENRIQUE[0], crm=crm(HENRIQUE),
        diagnostico="Lombalgia aguda", cid="M54.5",
        medicamentos=[
            ("Paracetamol", "750 mg", "oral", "2 comprimidos de 4 em 4 horas, se dor"),
            ("Cloridrato de ciclobenzaprina", "5 mg", "oral", "1 comprimido à noite por 5 dias"),
        ],
        destino=REVISAO, auditoria=True),
    cid_aceitos=["M54.5"],
    motivo="2 comprimidos de 750 mg a cada 4 horas somam até 9 g por dia, mais que o dobro do máximo "
           "de 4 g para adultos."))

CASOS.append(Caso(
    id="SINT-021", cenario="ambiguo", formato="pdf_digital", degradacao="nenhuma",
    canal_origem="Ambulatorio",
    documento=Doc(
        *SERRA_VERDE, titulo="LAUDO DE ULTRASSONOGRAFIA",
        campos=[("Paciente", ""), ("Idade", "52 anos"), ("Solicitante", solicitante(MARINA)),
                ("Data do exame", "21/10/2026")],
        blocos=[
            ("secao", "Ultrassonografia de abdome total"),
            ("par", "Indicação clínica: dor em hipocôndrio direito após as refeições."),
            ("secao", "Achados"),
            ("par", "Fígado de dimensões normais, com aumento difuso da ecogenicidade. Vesícula biliar com "
                    "cálculo móvel de 1,2 cm, paredes finas, sem sinais de inflamação. Vias biliares sem "
                    "dilatação. Pâncreas, baço e rins sem alterações."),
            ("secao", "Impressão diagnóstica"),
            ("par", "Esteatose hepática grau I. Colelitíase, sem sinais de colecistite."),
        ],
        assinatura=assinatura(LUISA)),
    esperado=gabarito(
        tipo="Laudo de Exame de Imagem", especialidade="Radiologia", prioridade="Rotina",
        paciente=None, idade=52, medico=MARINA[0], crm=crm(MARINA),
        exame="Ultrassonografia de abdome total",
        diagnostico="Colelitíase sem colecistite; esteatose hepática grau I", cid="K80.2",
        destino=REVISAO, auditoria=True),
    cid_aceitos=["K80.2", "K76.0"],
    campos_ausentes=["paciente.nome"],
    motivo="Laudo sem o nome do paciente: não dá para anexar ao prontuário de ninguém."))

CASOS.append(Caso(
    id="SINT-022", cenario="ambiguo", formato="pdf_escaneado", degradacao="scan_pesado",
    canal_origem="Central_Autorizacoes",
    documento=Guia(
        operadora=OPERADORA, registro_ans=REGISTRO_ANS, numero_guia="2026-0009377",
        carteira="0 8812 027716 15 4", beneficiario="Rodrigo Almeida Kühn",
        contratado="Centro de Endoscopia Digestiva Alto Paraná", profissional=LEONARDO[0], conselho="CRM",
        numero_conselho="", uf=LEONARDO[2], cbo="225165", carater="1 - Eletiva",
        data_solicitacao="22/10/2026", indicacao_clinica="",
        procedimentos=[("22", "99000981", "Colonoscopia com biópsia", "1")]),
    esperado=gabarito(
        tipo="Guia de Solicitação de Procedimento", especialidade="Gastroenterologia", prioridade="Rotina",
        paciente="Rodrigo Almeida Kühn", idade=None, medico=LEONARDO[0], crm=None,
        exames_solicitados=["Colonoscopia com biópsia"], destino=REVISAO, auditoria=True),
    cid_aceitos=[None],
    campos_ausentes=["medico_solicitante.crm", "indicação clínica"],
    motivo="Guia sem número do CRM e sem indicação clínica: a auditoria não tem como avaliar o pedido."))

CASOS.append(Caso(
    id="SINT-023", cenario="ambiguo", formato="pdf_escaneado", degradacao="scan_leve",
    canal_origem="Internacao",
    documento=Doc(
        *AURORA, titulo="RELATÓRIO DE ALTA HOSPITALAR",
        campos=[("Paciente", "Vera Lúcia Moraes"), ("Idade", "39 anos"),
                ("Data de nascimento", "12/03/1952"), ("Prontuário", "0051877"),
                ("Unidade", "Ortopedia - 5º andar"), ("Internação", "02/10/2026"), ("Alta", "09/10/2026")],
        blocos=[
            ("secao", "Diagnóstico principal"),
            ("par", "Fratura do colo do fêmur esquerdo (CID-10 S72.0)."),
            ("secao", "Resumo da internação"),
            ("par", "Paciente de 74 anos, admitida após queda da própria altura em casa, com dor e "
                    "incapacidade de apoiar o membro inferior esquerdo. Radiografia confirmou fratura do colo "
                    "do fêmur. Submetida a artroplastia parcial do quadril esquerdo em 03/10/2026, sem "
                    "intercorrências."),
            ("secao", "Condições de alta"),
            ("par", "Alta em bom estado geral, deambulando com andador e auxílio."),
            ("secao", "Prescrição de alta"),
            ("med", "Enoxaparina sódica 40 mg", "30 seringas",
             "Aplicar 1 seringa por via subcutânea, uma vez ao dia, por 30 dias."),
            ("med", "Paracetamol 750 mg", "20 comprimidos", "Tomar 1 comprimido de 6 em 6 horas, se dor."),
            ("secao", "Orientações"),
            ("par", "Retorno ao ambulatório de ortopedia em 14 dias para retirada dos pontos. Fisioterapia "
                    "motora conforme orientação."),
        ],
        assinatura=assinatura(MAURO), local_data="Curitiba, 9 de outubro de 2026"),
    esperado=gabarito(
        tipo="Relatório de Alta", especialidade="Ortopedia", prioridade="Rotina",
        paciente="Vera Lúcia Moraes", idade=None, medico=MAURO[0], crm=crm(MAURO),
        diagnostico="Fratura do colo do fêmur esquerdo", cid="S72.0",
        medicamentos=[
            ("Enoxaparina sódica", "40 mg", "subcutânea", "1 seringa uma vez ao dia por 30 dias"),
            ("Paracetamol", "750 mg", "oral", "1 comprimido de 6 em 6 horas, se dor"),
        ],
        destino=REVISAO, auditoria=True),
    cid_aceitos=["S72.0"],
    campos_ausentes=["paciente.idade (conflito: 39 no cabeçalho; 74 no texto e na data de nascimento)"],
    armadilha="Um extrator que pega o primeiro campo 'Idade' devolve 39 sem perceber o conflito.",
    motivo="Idade do cabeçalho (39) não bate com a data de nascimento nem com o texto (74 anos): pode ser "
           "documento de outra paciente."))

CASOS.append(Caso(
    id="SINT-024", cenario="ambiguo", formato="imagem", degradacao="scan_leve",
    canal_origem="Ambulatorio",
    documento=Doc(
        "Pronto Atendimento Vila Ipê", "Rua Ipê Roxo, 77 - Curitiba/PR", titulo="ATESTADO MÉDICO",
        tamanho="A5", campos=[],
        blocos=[
            ("impresso", "Atesto, para os devidos fins, que o(a) Sr.(a)"),
            ("mao", "Felipe Augusto Rocha", 250),
            ("impresso", "esteve sob meus cuidados profissionais nesta data, devendo"),
            ("impresso", "afastar-se de suas atividades pelo período de"),
            ("mao", "{{RASURA:2>12}} dias", 90),
            ("impresso", "a partir desta data."),
        ],
        assinatura=[], local_data="Curitiba, 22/10/2026",
        carimbo=[REGINA[0], REGINA[3], linha_crm(REGINA)], borrao_no_carimbo=True),
    esperado=gabarito(
        tipo="Atestado Médico", especialidade="Clínica Médica", prioridade="Rotina",
        paciente="Felipe Augusto Rocha", idade=None, medico=REGINA[0], crm=None,
        destino=REVISAO, auditoria=True, extras={"dias_afastamento": None}),
    cid_aceitos=[None],
    campos_ausentes=["dias_afastamento (rasurado: 2 ou 12)", "medico_solicitante.crm (borrado no carimbo)"],
    motivo="Número de dias rasurado e CRM borrado no carimbo: atestado rasurado não pode ser aceito sem "
           "confirmação."))

# ============================== URGÊNCIA + AMBIGUIDADE ======================================

CASOS.append(Caso(
    id="SINT-025", cenario="urgencia", formato="pdf_escaneado", degradacao="scan_leve",
    canal_origem="Pronto_Socorro",
    documento=Doc(
        *AURORA_RX, titulo="LAUDO DE TOMOGRAFIA COMPUTADORIZADA",
        campos=[("Paciente", ""), ("Idade", "58 anos"), ("Atendimento", "2026-PS-08833"),
                ("Solicitante", solicitante(GUSTAVO)), ("Data do exame", "22/10/2026")],
        blocos=[
            ("secao", "Angiotomografia de tórax (protocolo para tromboembolismo pulmonar)"),
            ("par", "Indicação clínica: dispneia e taquicardia de início súbito; trombose venosa profunda na "
                    "perna esquerda diagnosticada há 2 dias."),
            ("secao", "Achados"),
            ("par", "Falhas de enchimento em ramos segmentares e subsegmentares do lobo inferior esquerdo. "
                    "Ventrículo direito de dimensões normais. Sem derrame pleural."),
            ("secao", "Impressão diagnóstica"),
            ("par", "Tromboembolismo pulmonar agudo segmentar à esquerda, sem sinais de sobrecarga "
                    "ventricular direita."),
            ("par", "Resultado crítico comunicado ao médico assistente às 16h50."),
        ],
        assinatura=assinatura(LUISA)),
    esperado=gabarito(
        tipo="Laudo de Exame de Imagem", especialidade="Radiologia / Pneumologia", prioridade="Urgente",
        paciente=None, idade=58, medico=GUSTAVO[0], crm=crm(GUSTAVO), exame="Angiotomografia de tórax",
        diagnostico="Tromboembolismo pulmonar agudo segmentar à esquerda", cid="I26.9",
        destino=EMERGENCIA, auditoria=True, alerta=True),
    cid_aceitos=["I26.9"],
    campos_ausentes=["paciente.nome"],
    armadilha="Urgente e incompleto ao mesmo tempo. A urgência vem primeiro.",
    decisao_pendente="No grafo do README a checagem de urgência vem antes e o ramo de emergência não marca "
                     "revisão humana. Proposta: o ramo de emergência também marca requer_auditoria_humana "
                     "quando falta dado obrigatório (o plantão identifica pelo número de atendimento).",
    motivo="TEP agudo sem nome do paciente: alerta ao plantão já, e revisão humana em paralelo."))
