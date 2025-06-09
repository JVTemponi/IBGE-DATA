# main.py
from datetime import datetime
import config
import data_functions
import db_functions as db

def run_pipeline():
    """Executa o pipeline completo de extração, transformação e carga."""
    
    # # 1. Obtém os dados já processados com uma única chamada de função
    df_final = data_functions.ibge_mun_pop(
        config.FAIXAS_ETARIAS, 
        config.SIDRA_API_POP
    )
    
    if df_final.empty:
        print("Pipeline encerrado pois não foram encontrados dados.")
        return

    print("\nDataFrame final pronto para ser carregado:")
    print(df_final.head())
    
    # 2. Carrega os dados no Banco de Dados (lógica do db)
    engine = db.create_db_engine(config.DB_CONFIG)
    #db.create_tables(engine)
    #db.load_dataframe_to_tables(df_final, 'bi_populacao_por_faixa_etaria', engine)

    data_hoje = datetime.now().strftime("%Y-%m-%d")
    caminho_arquivo_csv = f"dados_exportados/populacao_ibge_{data_hoje}.csv"
    
    db.save_dataframe_to_csv(df_final, caminho_arquivo_csv)


    print(db.query_execute(config.QUERY_CIDADES_MG, engine))

if __name__ == "__main__":
    run_pipeline()