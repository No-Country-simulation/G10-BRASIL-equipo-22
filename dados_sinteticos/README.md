# Dados sintéticos do MediFlow

25 documentos clínicos **fictícios**, cada um com a saída que o agente deveria produzir (o gabarito).
Servem para três coisas:

1. **Desenvolver** o motor de extração e o grafo contra entradas variadas, sem dado real de paciente
   (dado de saúde é dado pessoal sensível na LGPD; nada aqui identifica ninguém).
2. **Demonstrar** os três cenários obrigatórios do desafio: rotina, urgência e ambiguidade com revisão humana.
3. **Medir** a qualidade: comparar a saída do agente com o gabarito, campo a campo.

Todo documento traz no rodapé *"DOCUMENTO FICTÍCIO - dados sintéticos para teste do MediFlow (Equipo 22)"*.

## O que tem aqui

```
dados_sinteticos/
├── documentos/      as entradas: SINT-xxx.pdf, .jpg ou .json
├── gabarito/        a saída esperada de cada documento (SINT-xxx.json)
├── manifesto.csv    uma linha por documento: arquivo, formato, cenário, destino esperado
├── casos.py         o conteúdo de cada documento e o gabarito (a fonte de tudo)
├── modelo.py        estruturas, destinos e a transcrição de referência
├── desenho.py       desenho em PDF, simulação de scanner e de foto de celular
├── gerar.py         gera tudo e confere a coerência antes de gravar
└── fontes/          duas fontes manuscritas, com as licenças
```

### Cobertura

| | texto | PDF digital | PDF escaneado | imagem | total |
|---|---|---|---|---|---|
| **rotina** | 2 | 4 | 1 | 3 | 10 |
| **urgência** | 2 | 2 | 3 | 1 | 8 |
| **ambíguo** | 1 | 2 | 2 | 2 | 7 |

Os seis tipos de documento do desafio aparecem: receituário, laudo laboratorial, laudo de imagem, guia de
solicitação (SP/SADT, no espírito do TISS), relatório de alta e atestado. Dois são escritos à mão
(SINT-010 legível, SINT-018 com uma palavra ilegível), quatro são fotos de celular e um é um scan ruim.

### Os 25 casos

| Caso | Tipo | Formato | Cenário | Destino esperado | Por quê |
|---|---|---|---|---|---|
| SINT-001 | Receituário | PDF digital | rotina | Farmacia_Hospitalar | Receita completa, doses habituais |
| SINT-002 | Receituário | texto | rotina | Farmacia_Hospitalar | Receita completa com diagnóstico e CID |
| SINT-003 | Laudo laboratorial | PDF digital | rotina | Prontuario_Eletronico | Hemograma normal |
| SINT-004 | Laudo laboratorial | PDF escaneado | rotina | Prontuario_Eletronico | Diabetes com valores alterados, nenhum crítico |
| SINT-005 | Laudo de imagem | texto | rotina | Prontuario_Eletronico | Radiografia normal |
| SINT-006 | Guia SP/SADT | PDF digital | rotina | Auditoria_Autorizacoes | Pedido eletivo completo |
| SINT-007 | Relatório de alta | PDF digital | rotina | Prontuario_Eletronico | Alta de paciente estável |
| SINT-008 | Atestado | foto | rotina | Prontuario_Eletronico | Atestado completo |
| SINT-009 | Receituário | imagem escaneada | rotina | Farmacia_Hospitalar | Receita de uso contínuo |
| SINT-010 | Receituário | foto, à mão | rotina | Farmacia_Hospitalar | Manuscrita, mas legível |
| SINT-011 | Laudo de imagem | texto | urgência | Fila_Emergencia_Medica | TEP agudo com sobrecarga do VD |
| SINT-012 | Laudo de imagem | PDF digital | urgência | Fila_Emergencia_Medica | AVC hemorrágico com desvio da linha média |
| SINT-013 | Laudo laboratorial | PDF escaneado | urgência | Fila_Emergencia_Medica | Potássio 6,9 mEq/L |
| SINT-014 | Laudo laboratorial | foto | urgência | Fila_Emergencia_Medica | Troponina 50 vezes acima da referência |
| SINT-015 | Laudo de imagem | PDF digital | urgência | Fila_Emergencia_Medica | Pneumotórax hipertensivo |
| SINT-016 | Guia SP/SADT | PDF escaneado | urgência | Auditoria_Autorizacoes ⚠️ | Pedido urgente: suspeita de dissecção de aorta |
| SINT-017 | Laudo laboratorial | texto | urgência | Fila_Emergencia_Medica | Hemoglobina 5,8 g/dL |
| SINT-018 | Receituário | foto, à mão | ambíguo | Fila_Revisao_Humana | Segundo medicamento ilegível e sem dose |
| SINT-019 | Receituário | PDF digital | ambíguo | Fila_Revisao_Humana | Metotrexato diário (o uso é semanal): alto risco |
| SINT-020 | Receituário | texto | ambíguo | Fila_Revisao_Humana | Paracetamol até 9 g/dia, máximo é 4 g |
| SINT-021 | Laudo de imagem | PDF digital | ambíguo | Fila_Revisao_Humana | Sem o nome do paciente |
| SINT-022 | Guia SP/SADT | PDF escaneado ruim | ambíguo | Fila_Revisao_Humana | Sem número do CRM e sem indicação clínica |
| SINT-023 | Relatório de alta | PDF escaneado | ambíguo | Fila_Revisao_Humana | Idade 39 no cabeçalho, 74 no texto |
| SINT-024 | Atestado | imagem escaneada | ambíguo | Fila_Revisao_Humana | Dias rasurados (2 ou 12) e CRM borrado |
| SINT-025 | Laudo de imagem | PDF escaneado | urgência | Fila_Emergencia_Medica + revisão ⚠️ | TEP agudo sem o nome do paciente |

⚠️ = depende de decisão da equipe (ver abaixo).

## Formato das entradas

- **Texto** (`.json`): o mesmo formato de requisição do README do projeto, com `tipo_arquivo: "TEXTO"`.
- **PDF digital**: tem camada de texto (dá para extrair sem OCR).
- **PDF escaneado**: só imagem, sem camada de texto, como sai de um scanner.
- **Imagem** (`.jpg`): scan ou foto de celular em perspectiva, sobre a mesa.

O `documento_id` e o `canal_origem` de cada arquivo estão no `manifesto.csv`.

## Formato do gabarito

Cada `gabarito/SINT-xxx.json` segue o contrato de saída do README (seção 2.3) e acrescenta um bloco
`_avaliacao`, que não faz parte da saída do agente:

| Campo de `_avaliacao` | Para que serve |
|---|---|
| `cenario`, `formato`, `degradacao`, `arquivo` | Identificam o caso |
| `motivo` | Por que o destino é esse |
| `armadilha` | O erro que o caso foi feito para pegar |
| `cid_aceitos` | CIDs que contam como certos (`null` incluído quando o documento não traz diagnóstico) |
| `campos_ausentes` | O que falta, está ilegível ou é contraditório no documento |
| `decisao_pendente` | Ponto em que a equipe ainda precisa decidir |
| `transcricao` | O texto do documento, para separar erro de leitura de erro de extração |

**Onde o documento não traz a informação, o gabarito tem `null`.** Inventar um valor conta como erro.

Sugestão para a avaliação: comparar com rigor `tipo_documento`, `nivel_prioridade`, `destino_principal`,
`requer_auditoria_humana`, nome do paciente, idade e CRM; medicamentos pelo par nome + dosagem; CID por
`cid_aceitos`; diagnóstico, exame e posologia com tolerância (sinônimos e abreviações);
`especialidade` não entra na nota. A métrica que mais importa é o **recall de urgência**: quantos dos
8 casos urgentes foram parar na fila de emergência.

## Regras de roteamento usadas (proposta)

1. **Laudo ou resultado com achado crítico** → `Fila_Emergencia_Medica`, com alerta ao plantão.
   Se também faltar dado obrigatório, marca `requer_auditoria_humana` (SINT-025).
2. **Senão, se houver problema** (falta identificação ou CRM, dado ilegível, rasurado ou contraditório,
   prescrição de alto risco ou dose acima do máximo) → `Fila_Revisao_Humana`.
3. **Senão, pelo tipo**: receituário → `Farmacia_Hospitalar`; guia → `Auditoria_Autorizacoes`;
   laudo, alta e atestado → `Prontuario_Eletronico`.

Prioridade: só `Rotina` e `Urgente`, como no exemplo do README.

### Decisões pendentes

- **SINT-016**: guia com caráter de urgência. Aqui vai para a auditoria de autorizações com prioridade
  `Urgente`; pelo grafo do README, toda urgência iria para a fila de emergência.
- **SINT-025**: no grafo do README, o ramo de emergência não marca revisão humana. Proposta: marcar quando
  faltar dado obrigatório.
- **Nomes dos destinos** além de `Fila_Emergencia_Medica` (o único que aparece no README).
- **`medico_solicitante`** é quem pediu, prescreveu ou emitiu. No laudo é quem pediu o exame, não o médico
  que assina o laudo (SINT-003 e SINT-011 testam isso).

## Como gerar de novo

```bash
cd dados_sinteticos
uv venv --python 3.12
uv pip install -r requirements-dados.txt
.venv/bin/python gerar.py
```

`gerar.py` confere cada caso antes de gravar: se o gabarito citar um nome, CRM, medicamento, dose ou idade
que não está no documento, ou se o destino não bater com as regras acima, ele para e diz qual caso.
O resultado é sempre o mesmo, byte a byte (sementes fixas e metadados sem a data atual), então gerar de novo
não suja o `git diff`.

Para mudar um caso ou criar outro, edite `casos.py` e rode `gerar.py`.

O arquivo de dependências se chama `requirements-dados.txt` porque o `.gitignore` do projeto ignora
qualquer `requirements.txt`.

## Dados fictícios

Pacientes, médicos, números de CRM, instituições, endereços, a operadora "Saúde Integral Planos", o registro
ANS 419999, as carteiras e os códigos de procedimento (`99xxxxxx`) são inventados. **Não valide os CRMs no
cadastro do CFM.** Os medicamentos usam o nome genérico (DCB), sem marca.

## Licenças das fontes

- Kalam (letra legível): SIL Open Font License 1.1 (`fontes/Kalam-OFL.txt`)
- Homemade Apple (letra de médico): Apache License 2.0 (`fontes/HomemadeApple-LICENSE.txt`)
