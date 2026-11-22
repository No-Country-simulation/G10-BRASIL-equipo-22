BEGIN TRANSACTION;
CREATE TABLE clinico_audit_historico (
        documento_id       TEXT PRIMARY KEY,
        tipo_documento     TEXT NOT NULL,
        crm_medico         TEXT,
        paciente_nome      TEXT,
        prioridade         TEXT NOT NULL,
        score_confianca    REAL NOT NULL,
        requer_auditoria   INTEGER DEFAULT 0,
        payload_json       TEXT,
        data_criacao       TEXT DEFAULT CURRENT_TIMESTAMP
    );
INSERT INTO "clinico_audit_historico" VALUES('DOC-E2E-M4-001','Receituário Médico','NÃO_INFORMADO','Juliana Paes Dr','Revisao_Humana',0.69,1,'{"status": "retido_auditoria_humana", "documento_id": "DOC-E2E-M4-001", "classificacao": {"tipo_documento": "Receituário Médico", "especialidade": "Clínica Médica / Ambulatorial", "nivel_prioridade": "Revisao_Humana", "score_confianca_classificacao": 0.69}, "dados_extraidos": {"paciente": {"nome": "Juliana Paes Dr"}, "medico_solicitante": {}, "medicamentos_prescritos": ["Amoxicilina 500mg 8/8h por 7 dias"]}, "decisao_roteamento": {"destino_principal": "Fila_Revisao_Humana", "requer_auditoria_humana": true, "justificativa_roteamento": "Documento retido preventivamente para Auditoria Humana (Human-in-the-Loop): registro CRM do médico solicitante ausente ou incompleto (score=0.69 < 0.85).", "notificacao_gerada": {"canal": "Painel_Auditoria_HitL", "mensagem": "REVISÃO HUMANA NECESSÁRIA: Documento DOC-E2E-M4-001 aguardando validação clínica no painel Streamlit (registro CRM do médico solicitante ausente ou incompleto)."}}, "armazenamento_oci": {"bucket": "mediflow-documentos-clinicos", "caminho_objeto": "auditoria_humana/DOC-E2E-M4-001.json", "status_backup": "sucesso"}}','2026-11-22 22:03:18');
INSERT INTO "clinico_audit_historico" VALUES('DOC-E2E-M4-URG','Laudo de Exame de Imagem','145892-SP','Carlos Eduardo Mendes','Urgente',0.99,0,'{"status": "processado", "documento_id": "DOC-E2E-M4-URG", "classificacao": {"tipo_documento": "Laudo de Exame de Imagem", "especialidade": "Radiologia / Pneumologia", "nivel_prioridade": "Urgente", "score_confianca_classificacao": 0.99}, "dados_extraidos": {"paciente": {"nome": "Carlos Eduardo Mendes", "idade": 52}, "medico_solicitante": {"nome": "Dra. Renata Silveira", "crm": "145892-SP"}, "exame_realizado": "Tomografia de Torax com contraste", "diagnostico_principal": "Tromboembolismo Pulmonar Agudo (TEP)", "cid_sugerido": "I26.9"}, "decisao_roteamento": {"destino_principal": "Fila_Emergencia_Medica", "requer_auditoria_humana": false, "justificativa_roteamento": "Achado critico de alta gravidade (TEP agudo) detectado em paciente sintomatico.", "notificacao_gerada": {"canal": "Alerta_Plantao_Medico", "mensagem": "ALERTA URGENTE: Laudo critico de TEP Agudo para paciente Carlos Eduardo Mendes no Pronto-Socorro."}}, "armazenamento_oci": {"bucket": "mediflow-documentos-clinicos", "caminho_objeto": "processados/urgentes/DOC-E2E-M4-URG.json", "status_backup": "sucesso"}}','2026-11-22 22:03:18');
INSERT INTO "clinico_audit_historico" VALUES('DOC-REABRIR-001','Receituário Médico','CRM-SP 12345','Marcos Valério','Revisao_Humana',0.98,1,'{"documento_id": "DOC-REABRIR-001", "status": "processado", "classificacao": {"tipo_documento": "Receituário Médico", "especialidade": "Clínica Médica", "nivel_prioridade": "Rotina", "score_confianca_classificacao": 0.98}, "dados_extraidos": {"paciente": {"nome": "Marcos Valério"}, "medico_solicitante": {"crm": "CRM-SP 12345"}}, "decisao_roteamento": {"destino_principal": "Farmacia_Hospitalar", "requer_auditoria_humana": false, "justificativa_roteamento": "Aprovado automaticamente"}, "armazenamento_oci": {"caminho_objeto": "processados/rotina/DOC-REABRIR-001.json"}}','2026-11-22 22:03:19');
CREATE TABLE triagem_audit_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        documento_id TEXT UNIQUE NOT NULL,
                        timestamp TEXT NOT NULL,
                        tipo_documento TEXT,
                        especialidade TEXT,
                        prioridade TEXT,
                        score_confianca REAL,
                        paciente_nome TEXT,
                        medico_crm TEXT,
                        diagnostico_principal TEXT,
                        destino_principal TEXT,
                        requer_auditoria INTEGER,
                        caminho_oci TEXT,
                        provedor_ia TEXT,
                        status_final TEXT,
                        latencia_ms REAL
                    );
INSERT INTO "triagem_audit_log" VALUES(170,'DOC-CLIN-2026-8942','2026-11-22T19:03:11.568683','Laudo de Exame de Imagem','Radiologia / Pneumologia','Urgente',0.99,'Carlos Eduardo Mendes','145892-SP','Tromboembolismo Pulmonar Agudo (TEP)','Fila_Emergencia_Medica',0,'processados/urgentes/radiologia_pneumologia/DOC-CLIN-2026-8942.json','Fast-Path Heuristic Engine (<100ms)','processado',1.09);
INSERT INTO "triagem_audit_log" VALUES(171,'DOC-CLIN-2026-1001','2026-11-22T19:03:11.603503','Receituário Médico','Clínica Médica / Ambulatorial','Rotina',0.95,'Mariana Costa Souza','198432-SP','Amigdalite Bacteriana Aguda','Farmacia_Hospitalar',0,'processados/rotina/clinica_medica_ambulatorial/DOC-CLIN-2026-1001.json','Fast-Path Heuristic Engine (<100ms)','processado',1.2);
INSERT INTO "triagem_audit_log" VALUES(172,'DOC-CLIN-2026-5503','2026-11-22T19:03:20.642344','Receituário Médico','Clínica Médica / Ambulatorial','Revisao_Humana',0.15,'Roberto F','184930-SP','','Farmacia_Hospitalar',0,'auditoria_humana/clinica_medica_ambulatorial/DOC-CLIN-2026-5503.json','Fast-Path Heuristic Engine (<100ms)','aprovado_pos_auditoria',1.54999999999999982e+00);
CREATE INDEX idx_clinico_crm ON clinico_audit_historico(crm_medico);
CREATE INDEX idx_clinico_prioridade ON clinico_audit_historico(prioridade);
DELETE FROM "sqlite_sequence";
INSERT INTO "sqlite_sequence" VALUES('triagem_audit_log',172);
COMMIT;