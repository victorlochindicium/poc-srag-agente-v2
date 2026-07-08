"""
Módulo responsável pela ingestão, higienização e anonimização dos dados do DATASUS.
Aplica allowlist para reter apenas colunas essenciais para o modelo.
"""
import pandas as pd
import sqlite3
import os

def preparar_banco_dados(caminho_csv_bruto: str, caminho_db: str = "srag_dados.db") -> None:
    """Lê o CSV bruto, limpa, anonimiza e salva no SQLite em uma única transação."""
    colunas_necessarias = ['DT_NOTIFIC', 'EVOLUCAO', 'UTI', 'VACINA']
    
    try:
        print("Iniciando processamento e anonimização (Allowlist)...")
        df = pd.read_csv(caminho_csv_bruto, sep=';', encoding='latin-1', usecols=colunas_necessarias, low_memory=False)
        
        # Conversão robusta de datas
        df['DT_NOTIFIC'] = pd.to_datetime(df['DT_NOTIFIC'], errors='coerce').dt.normalize()
        df = df.dropna(subset=['DT_NOTIFIC'])

        # Preenchimento de nulos com o padrão DATASUS (9 = Ignorado)
        for col in ['EVOLUCAO', 'UTI', 'VACINA']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(9).astype(int)
        
        # Conexão segura com Context Manager (fecha automaticamente)
        print("Criando banco de dados SQLite...")
        with sqlite3.connect(caminho_db) as conn:
            df.to_sql("internacoes", conn, if_exists="replace", index=False)
            
        print("Banco de dados pronto para o Agente!")
        
    except Exception as e:
        print(f"Erro no pipeline de dados: {e}")

if __name__ == "__main__":
    preparar_banco_dados("INFLUD26-04-05-2026.csv")
