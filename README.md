# AI Error Monitoring Pipeline v2
 
Pipeline de monitoramento contínuo de erros de um sistema de IA responsável por extrair informações de documentos societários.
 
Esta versão introduz um banco de dados PostgreSQL como camada de persistência, um orquestrador de execução, e um dashboard interativo construído em Python com Streamlit — substituindo a exportação para Excel e o Power BI da versão anterior.
 
> A versão anterior do projeto está disponível em [ai-error-monitoring-pipeline-v1](https://github.com/Mayradias/ai-error-monitoring-pipeline-v1)
 
---
 
## Visão Geral do Projeto
 
Este projeto foi desenvolvido para monitorar o desempenho de um sistema de IA responsável por extrair informações estruturadas de documentos societários enviados para um portal de registro empresarial.
 
Quando a IA falha na extração correta das informações, o documento é revisado por um humano que registra um **motivo de rejeição** explicando o erro encontrado.
 
Cada protocolo pode ter dois status principais:
 
- **Aprovado**
- **Rejeitado**

  
O objetivo do projeto é:
 
- automatizar a coleta dos motivos de rejeição e dos protocolos aprovados
- persistir os dados em banco de dados relacional
- classificar os erros cometidos pela IA automaticamente
- monitorar o desempenho do modelo ao longo do tempo
- identificar oportunidades de treinamento direcionado do modelo
---
 
## Arquitetura do Pipeline
 
```
Orquestrador (orquestrador.py)
        │
        ├── 1. Automação APROVADOS (Selenium)
        │         └── protocolos_aprovados.txt
        │
        ├── 2. Automação REJEITADOS (Selenium)
        │         └── motivos_rejeicao.txt
        │
        └── 3. Pipeline Banco (pipeline_banco.py)
                  ├── Classificação automática dos erros
                  └── Inserção no PostgreSQL
                            │
                            └── Dashboard Streamlit (dashboard.py)
```
 
O pipeline segue cinco etapas principais:
 
1. Coleta automática dos protocolos aprovados
2. Coleta automática dos motivos de rejeição
3. Classificação automática dos erros
4. Persistência no banco de dados PostgreSQL
5. Visualização interativa via dashboard Streamlit
---
 
## Dashboard de Monitoramento
 
O dashboard é construído em Python com Streamlit e Plotly, conectando diretamente ao banco de dados PostgreSQL.
 
### KPIs
 
- Total de protocolos únicos aprovados
- Total de seções aprovadas
- Total de protocolos rejeitados
- Taxa de aprovação geral
### Visualizações
 
- Aprovados vs Rejeitados — gráfico de rosca com total no centro
- Tipo de erro — proporção entre erros de extração, alucinação e não classificados
- Categorias de erro — ranking de frequência por categoria com filtro interativo
### Filtros disponíveis
 
- Período (mês)
- Seção do documento (Assinantes, Preâmbulo, Feixos, Cláusulas, Consolidação)
- Exibir ou ocultar erros não classificados
---
 
## Automação Web
 
A coleta foi automatizada utilizando **Python e Selenium**, com dois scripts independentes:
 
### Aprovados (`automationAPROVADOS.py`)
 
Extrai para cada protocolo aprovado:
- Número do protocolo
- Seção
- Data de aprovação
### Rejeitados (`automationcollect_rejection_reasons.py`)
 
Extrai para cada protocolo rejeitado:
- Número do protocolo
- Seção
- Data de rejeição
- Motivo de rejeição

  
O fluxo inicial é iniciado manualmente pelo usuário — login, filtro e consulta. A partir desse ponto o script assume o controle da navegação e coleta todos os registros automaticamente, página a página.
 
---
 
## Desafios Técnicos
 
Durante o desenvolvimento da automação foram enfrentados desafios comuns em aplicações web modernas baseadas em frameworks frontend.
 
**Problemas encontrados:**
- `StaleElementReferenceException`
- `ElementClickInterceptedException`
- Recriação do DOM após navegação
- Carregamento assíncrono da tabela
- Paginação dinâmica

  
**Soluções implementadas:**
- Relocalização de elementos por identificador único (PID) — elimina StaleElement definitivamente
- Espera ativa para estabilização da tabela
- Funções robustas de clique com múltiplas tentativas
- Controle de registros processados por página
---
 
## Classificação de Erros
 
O sistema de classificação utiliza **RapidFuzz** com uma lógica hierárquica de prioridade:
 
### Estrutura de prioridade
 
```
1. Detecta "alucinação/alucinou"
        └── Aplica regras de alucinação → retorna imediatamente
 
2. Aplica regras compostas (combinação de palavras-chave)
        └── Ao encontrar match → retorna imediatamente
 
3. Aplica regras simples (palavra-chave isolada)
        └── Ao encontrar match → retorna imediatamente
 
4. "Outros" — caso nenhuma regra encontre match
```
 
### Regras simples
 
Detectam palavras-chave únicas de cada categoria. Exemplos:
 
| Palavra-chave | Categoria |
|---|---|
| cabeçalho, nire, cnpj | Erro de extração no cabeçalho |
| preâmbulo | Erro de extração no preâmbulo |
| feixos | Erro de extração no feixos |
| logradouro, bairro, cep, complemento | Erro de extração no endereço |
| enquadramento | Erro de extração no enquadramento |
| quotas, capital | Erro na alteração de capital e quotas |
 
### Regras compostas
 
Detectam combinações de palavras que indicam um erro específico. Exemplos:
 
| Combinação | Categoria |
|---|---|
| nome + sócio | Erro de extração nos dados do sócio |
| nome + empresa | Erro de extração no nome da empresa |
| entrada + sócio | Erro na extração de entrada/saída de sócios |
| junto + objeto | Erro de espaçamento ou junção de palavras |
 
### Subcategorias de alucinação
 
- Alucinação na data e local de assinatura
- Alucinação no nome da empresa
- Alucinação no nome do sócio
- Alucinação no endereço
- Alucinação no representante legal
- Alucinação no capital social
- Alucinação nos assinantes
---
 
## Banco de Dados
 
### Tabela: `protocolos`
 
| Campo | Tipo | Descrição |
|---|---|---|
| id | SERIAL | Chave primária |
| numero_protocolo | TEXT | Número do protocolo |
| secao | TEXT | Seção do documento |
| status | TEXT | APROVADO ou REJEITADO |
| data_protocolo | TIMESTAMP | Data do protocolo |
| motivo_rejeicao | TEXT | Motivo registrado pelo revisor |
| categoria | TEXT | Categoria classificada automaticamente |
| tipo_erro | TEXT | Erro de extração, alucinação ou não classificado |
| inserido_em | TIMESTAMP | Data de inserção no banco |
 
Protocolos aprovados entram com `motivo_rejeicao`, `categoria` e `tipo_erro` = `N/A`.
 
### Tabela: `execucoes_pipeline`
 
Registra cada execução do pipeline com totais inseridos e status de sucesso ou erro.
 
### Deduplicação
 
O pipeline verifica `numero_protocolo + secao + categoria + data_protocolo` antes de inserir — evita duplicatas em execuções semanais consecutivas.
 
---
 
## Estrutura do Projeto
 
```
ai-error-monitoring-pipeline/
│
├── automation/
│   ├── automationAPROVADOS.py
│   └── automationcollect_rejection_reasons.py
│
├── pipeline/
│   └── pipeline_banco.py
│
├── dashboard/
│   └── dashboard.py
│
├── orchestrator/
│   └── orquestrador.py
│
├── sample_data/
│   ├── motivos_rejeicao_exemplo.txt
│   └── protocolos_aprovados_exemplo.txt
│
├── images/
│   └── architecture_diagram.png
│
├── requirements.txt
└── README.md
```
 
---
 
## Tecnologias Utilizadas
 
- Python
- Selenium + WebDriver Manager
- RapidFuzz
- PostgreSQL
- psycopg2
- Pandas
- Streamlit
- Plotly
---
 
## Como Executar o Projeto
 
### Pré-requisitos
 
- Python 3.10+
- PostgreSQL instalado e rodando
- Google Chrome instalado
### Instalação
 
```bash
git clone https://github.com/Mayradias/ai-error-monitoring-pipeline.git
cd ai-error-monitoring-pipeline
pip install -r requirements.txt
```
 
### Configuração do banco
 
Crie o banco de dados no PostgreSQL:
 
```sql
CREATE DATABASE ai_error_monitoring;
```
 
Configure a senha nos arquivos `pipeline_banco.py` e `dashboard.py`:
 
```python
password="sua_senha_aqui"
```
 
### Execução
 
```bash
# Rodar o pipeline completo
python orchestrator/orquestrador.py
 
# Rodar apenas o dashboard
streamlit run dashboard/dashboard.py
```
 
---
 
## Resultados Obtidos
 
A análise dos dados permitiu identificar falhas recorrentes e orientar treinamentos específicos do modelo de IA.
 
Após a implementação de treinamentos direcionados para determinados tipos de erro, foram observadas melhorias significativas na taxa de acerto do sistema:
 
- Aumento de **15 pontos percentuais** na acurácia geral
- Redução de **80%** em erros de alucinação
- Redução de **75%** nos erros de extração
- Diminuição da variabilidade de erros ao longo do tempo
A análise histórica demonstrou que **treinamentos direcionados com base na análise sistemática de erros podem reduzir significativamente falhas recorrentes, mesmo em IAs altamente treinadas**.
 
---
 
## Observações
 
Todos os dados utilizados neste repositório foram **anonimizados ou simulados** para preservar a confidencialidade das informações reais.
 
As URLs do portal, credenciais de acesso e dados sensíveis foram removidos do código antes da publicação.
 
