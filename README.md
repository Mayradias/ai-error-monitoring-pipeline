# AI Error Monitoring Pipeline

Pipeline de monitoramento e análise de erros gerados por um sistema de Inteligência Artificial responsável por extrair informações de documentos societários processados em um portal de registro empresarial.

Este projeto automatiza a coleta de motivos de rejeição de documentos analisados pela IA, estrutura os dados de erro e gera dashboards analíticos para monitorar o desempenho do modelo ao longo do tempo.

---
# Visão Geral do Projeto

Este projeto foi desenvolvido para monitorar o desempenho de um sistema de IA responsável por extrair informações estruturadas de documentos societários enviados para um portal de registro empresarial.

Quando a IA falha na extração correta das informações, o documento é revisado por um humano que registra um **motivo de rejeição** explicando o erro encontrado.

O objetivo do projeto é:

- automatizar a coleta dos motivos de rejeição
- estruturar os dados de erro
- classificar os erros cometidos pela IA
- monitorar o desempenho do modelo ao longo do tempo
- identificar oportunidades de treinamento direcionado do modelo

O pipeline integra **automação web, processamento de dados e visualização em BI**.

---
# Arquitetura do Pipeline

![Arquitetura do Pipeline](images/architecture_diagram.png)

O pipeline segue quatro etapas principais:

1. Coleta automática dos motivos de rejeição
2. Estruturação dos dados de erro
3. Classificação dos erros
4. Monitoramento analítico via dashboard

---

# Dashboard de Monitoramento

![Dashboard Preview](dashboard/dashboard_preview.png)

Os dados estruturados alimentam um **dashboard analítico** desenvolvido para monitorar o desempenho do sistema de IA.

O dashboard apresenta:

## Métricas gerais

- total de protocolos analisados
- percentual de erros
- percentual de acertos

---

## Classificação de erros

Ranking dos erros mais frequentes cometidos pela IA.

Exemplos:

- erro de extração no cabeçalho
- alucinação nos assinantes
- erro de extração nos assinantes
- erro de extração no preâmbulo

---

## Contexto do Projeto

Este projeto surgiu a partir da identificação de uma limitação na forma como os erros de um sistema de IA eram monitorados.

Embora os documentos rejeitados possuíssem motivos de erro registrados, essas informações não estavam estruturadas de forma que permitisse análise sistemática ou acompanhamento da performance do modelo ao longo do tempo.

A partir dessa observação, foi desenvolvido um pipeline de coleta, estruturação e análise desses dados, permitindo transformar registros operacionais em métricas analíticas.

---

# Features 

- Automação da coleta de motivos de rejeição em portal web
- Extração estruturada de informações a partir de registros de erro
- Classificação automática de erros utilizando similaridade textual
- Monitoramento visual da performance da IA
- Identificação de padrões de falha para orientar treinamento do modelo
- Pipeline completo: **coleta → processamento → análise**

---

# Fonte dos Dados

Os dados são coletados de um **portal corporativo de processamento de documentos**, onde protocolos analisados por um sistema de IA são listados.

Cada protocolo pode ter dois status principais:

- **Aprovado**
- **Rejeitado**

Quando um protocolo é rejeitado, um revisor humano registra um **motivo de rejeição**, explicando o erro identificado no processamento automático.

Exemplo de motivo de rejeição: IA não extraiu CNPJ do cabeçalho

---

# Automação Web

A coleta dos motivos de rejeição foi automatizada utilizando **Python e Selenium**.

O fluxo inicial é iniciado manualmente pelo usuário:
1. Login no portal
2. Acesso à área de documentos
3. Aplicação de filtros para protocolos rejeitados
4. Execução da consulta

A partir desse ponto, o script assume o controle da navegação.

Para cada protocolo listado, o script executa:
1. Abrir os detalhes do protocolo
2. Acessar a interface de rejeição
3. Ler o campo contendo o motivo de rejeição
4. Extrair o texto
5. Salvar o motivo
6. Retornar à lista de protocolos
7. Continuar para o próximo registro

---

# Desafios Técnicos
Durante o desenvolvimento da automação foram enfrentados desafios comuns em aplicações web modernas baseadas em frameworks frontend.

Principais problemas encontrados:

- `StaleElementReferenceException`
- `ElementClickInterceptedException`
- recriação do DOM após navegação
- carregamento assíncrono da tabela
- paginação dinâmica

Soluções implementadas:

- espera ativa para estabilização da tabela
- relocalização dos elementos após navegação
- funções robustas de clique
- identificação dos registros processados para evitar duplicação

---

# Saída Bruta da Automação

O script gera um arquivo texto contendo os motivos de rejeição extraídos.

Arquivo gerado: **motivos_rejeicao.txt**

Exemplo de estrutura:
RELATÓRIO – MOTIVOS DE REJEIÇÃO
Protocolo 0001
Erro de extração no cabeçalho
Protocolo 0002
Alucinação nos assinantes

---

# Processamento e Estruturação dos Dados

Após a coleta, o arquivo TXT é transformado em um dataset estruturado.

Utilizando **Pandas** e **RapidFuzz**, os motivos de rejeição são classificados em categorias de erro.

Exemplos de categorias:

- erro de extração no cabeçalho
- erro de extração nos assinantes
- alucinação nos assinantes
- erro de extração no preâmbulo
- erro de extração no objeto social

A partir dessas categorias são geradas métricas como:

- taxa de erro da IA
- taxa de acerto
- distribuição dos tipos de erro
- evolução dos erros ao longo do tempo

---

# Resultados Obtidos

A análise dos dados permitiu identificar falhas recorrentes e orientar treinamentos específicos do modelo de IA.

Após a implementação de treinamentos direcionados para determinados tipos de erro, foram observadas melhorias significativas na taxa de acerto do sistema. Os principais foram: 
Aumento de 15 p.p na acurácia geral. 
Diminuição de 80% em erros de alucinação e 75% nos erros de extração. 
Diminuição da variabilidade de erros. 

A análise histórica demonstrou que **treinamentos direcionados podem reduzir significativamente a ocorrência desses erros mesmo em IA’s altamente treinadas**.

---

# Estrutura do Projeto

ai-error-monitoring-pipeline
│
├── automation
│ └── automationcollect_rejection_reasons.py
│
├── data processing
│ └── data_processingprocess_rejection_reasons.py
│
├── sample data
  └── motivo_rejeicao_exemplo.xlsx
  └── motivo_rejeicao_exemplo.txt
│
├── dashboard
│ └── dashboard_preview.png
│
├── images
│ └── architecture_diagram.png
│
├── requirements.txt
└── README.md


---

# Tecnologias Utilizadas

- Python
- Selenium
- Pandas
- RapidFuzz
- Power BI

---
# Como Executar o Projeto

1. Clone o repositório
git clone https://github.com/Mayradias/ai-error-monitoring-pipeline.git

2. Instale as dependências
pip install -r requirements.txt

3. Execute o script de automação
python automation/automation_collect_rejection_reasons.py

4. Execute o processamento dos dados
python data_processing/process_rejection_reasons.py

---
# Objetivo do Projeto

O objetivo deste projeto é criar um sistema de **monitoramento contínuo da qualidade de sistemas de IA**, permitindo:

- identificar rapidamente erros recorrentes
- orientar novos treinamentos do modelo
- medir o impacto de melhorias implementadas
- acompanhar a evolução da precisão da IA

---

# Observações

Todos os dados utilizados neste repositório foram **anonimizados ou simulados**, e nenhuma informação sensível ou proprietária foi incluída.
