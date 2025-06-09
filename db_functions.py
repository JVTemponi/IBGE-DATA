# database_handler.py

from sqlalchemy import create_engine, text
import pandas as pd
import os

def create_db_engine(db_config):
    user = db_config['user']
    password = db_config['password']
    host = db_config['host']
    name = db_config['name']
    return create_engine(f'mysql+mysqlconnector://{user}:{password}@{host}/{name}')

def create_tables(engine):
    sql = f"""
        CREATE TABLE IF NOT EXISTS bi_populacao_por_faixa_etaria (
            id INT AUTO_INCREMENT PRIMARY KEY,
            municipio VARCHAR(255) NOT NULL,
            uf CHAR(2) NOT NULL,
            pop_0_14 INT NOT NULL DEFAULT 0,
            pop_15_19 INT NOT NULL DEFAULT 0,
            pop_20_29 INT NOT NULL DEFAULT 0,
            pop_30_39 INT NOT NULL DEFAULT 0,
            pop_40_49 INT NOT NULL DEFAULT 0,
            pop_50_59 INT NOT NULL DEFAULT 0,
            pop_60_74 INT NOT NULL DEFAULT 0,
            pop_75_99 INT NOT NULL DEFAULT 0,
            pop_100_mais INT NOT NULL DEFAULT 0,
            pop_total INT NOT NULL DEFAULT 0,
            ultima_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY idx_municipio_uf (municipio, uf)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    
    try:
        with engine.connect() as connection:
            connection.execute(text(sql))
            connection.execute(text(f"TRUNCATE TABLE bi_populacao_por_faixa_etaria"))
            connection.commit()
    except Exception as e:
        print(f"Erro ao configurar a tabela: {e}")
        raise

def load_dataframe_to_tables(df, table_name, engine):
    try:
        df.to_sql(table_name, con=engine, if_exists='append', index=False)
        print(f"Dados inseridos com sucesso na tabela '{table_name}'!")
    except Exception as e:
        print(f"Erro ao inserir dados no banco: {e}")
        raise

def save_dataframe_to_csv(df, file_path):

    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        print(f"Salvando dados no arquivo CSV: {file_path}...")
        df.to_csv(
            file_path, 
            index=False,         # Essencial: Não salva o índice numérico do DataFrame como uma coluna no CSV.
            sep=';',             # Usa ponto e vírgula como separador. Ideal para abrir no Excel no Brasil/Europa.
            encoding='utf-8-sig' # Codificação que garante a correta exibição de acentos (ç, ã, é) ao abrir no Excel.
        )
    except Exception as e:
        print(f"Erro ao inserir dados no banco: {e}")
        raise

def query_execute(query, engine):

    print (f"Executando consulta: {query}")

    result_query = pd.read_sql_query(query, engine)
    return result_query