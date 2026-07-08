"""
Módulo principal do Agente Orquestrador.
Implementa a arquitetura ReAct usando LangGraph, com ferramentas dinâmicas e auditoria profissional.
"""
import os
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import logging
from datetime import datetime
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage
from langchain_community.tools import DuckDuckGoSearchRun

# 1. Configuração de Auditoria Profissional (Logging)
# Em vez de prints genéricos, criamos um log auditável com timestamp
logging.basicConfig(
    filename='auditoria.log',
    level=logging.INFO,
    format='%(asctime)s - [AUDITORIA] - %(levelname)s - %(message)s'
)

# 2. Definição das Ferramentas (Tools) Dinâmicas
@tool
def gerar_graficos_srag() -> str:
    """Gera gráficos de casos diários (últimos 30 dias) e mensais (últimos 12 meses) e os salva localmente."""
    logging.info("Ferramenta 'gerar_graficos_srag' acionada.")
    try:
        with sqlite3.connect("srag_dados.db") as conn:
            query = "SELECT DT_NOTIFIC FROM internacoes WHERE DT_NOTIFIC IS NOT NULL"
            df_datas = pd.read_sql_query(query, conn)
            
        df_datas['DT_NOTIFIC'] = pd.to_datetime(df_datas['DT_NOTIFIC'])
        data_maxima = df_datas['DT_NOTIFIC'].max()
        
        # Gráfico 30 dias
        data_30_dias = data_maxima - pd.Timedelta(days=30)
        df_30d = df_datas[df_datas['DT_NOTIFIC'] >= data_30_dias]
        contagem_diaria = df_30d.groupby(df_30d['DT_NOTIFIC'].dt.date).size()
        plt.figure(figsize=(10, 5))
        contagem_diaria.plot(kind='line', marker='o', color='#1f77b4')
        plt.title('Casos Diários (Últimos 30 dias)')
        plt.savefig('grafico_diario.png')
        plt.close()
        
        # Gráfico 12 meses
        data_12_meses = data_maxima - pd.DateOffset(months=12)
        df_12m = df_datas[df_datas['DT_NOTIFIC'] >= data_12_meses].copy()
        df_12m['Mes_Ano'] = df_12m['DT_NOTIFIC'].dt.to_period('M')
        contagem_mensal = df_12m.groupby('Mes_Ano').size()
        plt.figure(figsize=(10, 5))
        contagem_mensal.plot(kind='bar', color='#ff7f0e')
        plt.title('Casos Mensais (Últimos 12 meses)')
        plt.savefig('grafico_mensal.png')
        plt.close()
        
        logging.info("Gráficos gerados com sucesso.")
        return "Gráficos 'grafico_diario.png' e 'grafico_mensal.png' foram gerados com sucesso."
    except Exception as e:
        erro_msg = f"Erro ao gerar gráficos: {e}"
        logging.error(erro_msg)
        return erro_msg

@tool
def extrair_metricas_srag() -> str:
    """Consulta o banco de dados SQL e retorna métricas de mortalidade, ocupação UTI, vacinação e aumento de casos."""
    logging.info("Ferramenta 'extrair_metricas_srag' acionada.")
    try:
        with sqlite3.connect("srag_dados.db") as conn:
            mort = pd.read_sql_query("SELECT (CAST(SUM(CASE WHEN EVOLUCAO = 2 THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*)) * 100 AS taxa FROM internacoes WHERE EVOLUCAO IN (1, 2)", conn)['taxa'].iloc[0]
            uti = pd.read_sql_query("SELECT (CAST(SUM(CASE WHEN UTI = 1 THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*)) * 100 AS taxa FROM internacoes WHERE UTI IN (1, 2)", conn)['taxa'].iloc[0]
            vac = pd.read_sql_query("SELECT (CAST(SUM(CASE WHEN VACINA = 1 THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*)) * 100 AS taxa FROM internacoes WHERE VACINA IN (1, 2)", conn)['taxa'].iloc[0]
            
            query_aum = """
            WITH Datas AS (SELECT MAX(DT_NOTIFIC) as max_data FROM internacoes),
            Periodo_Atual AS (SELECT COUNT(*) as qtd FROM internacoes, Datas WHERE DT_NOTIFIC >= date(max_data, '-30 days')),
            Periodo_Anterior AS (SELECT COUNT(*) as qtd FROM internacoes, Datas WHERE DT_NOTIFIC >= date(max_data, '-60 days') AND DT_NOTIFIC < date(max_data, '-30 days'))
            SELECT p1.qtd as casos_recentes, p2.qtd as casos_antigos FROM Periodo_Atual p1, Periodo_Anterior p2
            """
            df_aum = pd.read_sql_query(query_aum, conn)
            recentes, antigos = df_aum['casos_recentes'].iloc[0], df_aum['casos_antigos'].iloc[0]
            aumento = ((recentes - antigos) / antigos) * 100 if antigos > 0 else 0
            
        resultado = f"Mortalidade: {mort:.2f}% | UTI: {uti:.2f}% | Vacinação: {vac:.2f}% | Aumento (30 dias): {aumento:.2f}%"
        logging.info(f"Métricas extraídas: {resultado}")
        return resultado
    except Exception as e:
        logging.error(f"Erro SQL: {e}")
        return "Falha ao extrair métricas do banco de dados."

@tool
def buscar_noticias_recentes(query: str = "últimas notícias surto SRAG Brasil") -> str:
    """Busca notícias recentes sobre SRAG no Brasil para fornecer contexto qualitativo."""
    logging.info(f"Ferramenta 'buscar_noticias_recentes' acionada com a query: {query}")
    try:
        search = DuckDuckGoSearchRun()
        resultado = search.run(query)
        logging.info("Notícias coletadas com sucesso via DuckDuckGo.")
        return resultado
    except Exception as e:
        logging.error(f"Erro na busca web: {e}")
        return "Falha ao buscar notícias na web."

def executar_agente():
    """Função principal que inicializa e orquestra o Agente."""
    # Validação de chave segura
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("Chave GOOGLE_API_KEY não encontrada nas variáveis de ambiente.")

    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest", temperature=0)
    ferramentas = [gerar_graficos_srag, extrair_metricas_srag, buscar_noticias_recentes]

    # Guardrails dinâmicos: Injetamos a data atual para evitar alucinação
    data_atual = datetime.now().strftime("%d/%m/%Y")
    prompt_sistema = f"""Você é um analista de dados especialista em saúde da Indicium HealthCare.
    A data de hoje é {data_atual}. Nunca alucine datas.
    Seu objetivo é escrever um relatório analítico sobre o surto de SRAG no Brasil em formato Markdown limpo.
    REGRAS (Guardrails):
    1. Use as ferramentas disponíveis para coletar dados, buscar notícias e gerar gráficos antes de responder.
    2. Nunca invente dados médicos. Responda APENAS sobre saúde e SRAG.
    3. Retorne APENAS o relatório formatado, sem estruturas de dicionário Python."""

    agente = create_react_agent(llm, ferramentas, prompt=prompt_sistema)
    
    logging.info("Iniciando execução do Agente LangGraph...")
    mensagem = "Escreva o relatório final com as métricas de SRAG, gere os gráficos e busque o contexto nas notícias."
    
    # Executando o grafo
    resultado_final = agente.invoke({"messages": [HumanMessage(content=mensagem)]})
    
    # Tratando o Output para exibir apenas o texto limpo (exigência do feedback)
    texto_relatorio = resultado_final["messages"][-1].content
    logging.info("Relatório gerado com sucesso e orquestração finalizada.")
    
    return texto_relatorio

if __name__ == "__main__":
    print("Iniciando Agente... Verifique o arquivo auditoria.log para detalhes.")
    relatorio = executar_agente()
    print("\n" + "="*50 + "\nRELATÓRIO FINAL\n" + "="*50)
    print(relatorio)
