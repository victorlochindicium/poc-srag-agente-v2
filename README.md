# Agente Orquestrador ReAct - Análise de Dados SRAG (Indicium HealthCare)

## Sobre o Projeto
Esta Prova de Conceito (PoC) apresenta um Agente Autônomo baseado na arquitetura **ReAct** (Reasoning and Acting) com LangGraph. O objetivo é fornecer uma análise situacional sobre a Síndrome Respiratória Aguda Grave (SRAG) no Brasil. 

Nesta versão refatorada, o foco foi garantir **segurança de dados, orquestração dinâmica completa e auditoria rastreável**, elevando a solução a padrões de produção.

## Arquitetura e Fluxo (LangGraph)
A arquitetura abandona execuções lineares e adota um fluxo de orquestração 100% dinâmico:
* **Usuário:** Envia o prompt inicial.
* **Orquestrador (LangGraph `create_react_agent`):** Recebe o contexto e entra em um loop de raciocínio (Thought -> Action -> Observation).
* **Cérebro (LLM):** Google Gemini (`gemini-1.5-flash-latest`), com guardrails de injeção de data para evitar alucinação temporal.
* **Ferramentas Dinâmicas (@tool):** Todas as ações foram convertidas em ferramentas invocadas sob demanda pelo agente:
  1. `extrair_metricas_srag`: Consulta segura ao banco de dados SQLite (com Context Managers).
  2. `buscar_noticias_recentes`: Consulta à web via DuckDuckGo.
  3. `gerar_graficos_srag`: Pipeline de visualização (Matplotlib/Pandas) gerido autonomamente pelo LLM.

## Critérios de Avaliação e Boas Práticas

1. **Tratamento de Dados e Clean Code:** Pipeline refatorado (`src/data_pipeline.py`) usando *allowlist* para 4 colunas essenciais, tratamento de nulos e datas, e gerenciamento seguro de conexões de banco de dados (`with sqlite3.connect...`).
2. **Segurança (Guardrails e Segredos):** - Uso rigoroso de `.gitignore` para impedir o vazamento de chaves e bases de dados locais.
   - A `GOOGLE_API_KEY` é exigida via variável de ambiente do SO, nunca em hardcode.
   - Guardrail de data injetado no *System Prompt* para forçar ancoragem temporal real.
3. **Governança e Transparência:** Implementação da biblioteca `logging` do Python. Toda decisão do agente (chamada de tools, parâmetros, queries SQL e erros) é registrada no arquivo local `auditoria.log` com *timestamps* precisos.
4. **Versionamento:** Fluxo de commits atômicos e descritivos.

## Como Executar o Projeto

1. **Clone o repositório:**
   ```bash
   git clone [https://github.com/SEU_USUARIO/poc-srag-agente-v2.git](https://github.com/SEU_USUARIO/poc-srag-agente-v2.git)
   cd poc-srag-agente-v2
