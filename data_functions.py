# data_handler.py

import pandas as pd
import sidrapy
from functools import reduce

def ibge_mun_pop(groups_data, api_params):
    
    dataframes_processados = []

    for group in groups_data:
        
        # Monta o dicionário 'classifications' para a chamada atual
        filtros_request = api_params.get('classifications', {}).copy()
        filtros_request['287'] = group['cod'] # Adiciona os códigos de idade
        
        try:
            print(f"Buscando dados para o grupo: {group['coluna']}...")
            df_raw = sidrapy.get_table(
                table_code=api_params['table_code'],
                territorial_level=api_params['territorial_level'],
                variable=api_params['variable'],
                ibge_territorial_code=api_params['ibge_territorial_code'],
                classifications=filtros_request
            )
            
            # Tratamento inicial do DataFrame recebido
            df_raw['V'] = pd.to_numeric(df_raw['V'], errors='coerce')
            df_processed = df_raw.groupby('D1N')['V'].sum().reset_index()
            df_processed = df_processed.rename(columns={'D1N': 'municipio', 'V': group['coluna']})
            
            dataframes_processados.append(df_processed)

        except Exception as e:
            print(f"Erro ao buscar ou processar o grupo {group['coluna']}: {e}")
            continue 

    df_final = reduce(lambda left, right: pd.merge(left, right, on='municipio', how='outer'), dataframes_processados)

    df_final = df_final.fillna(0)

    colunas_populacao = df_final.columns.drop('municipio')
    df_final[colunas_populacao] = df_final[colunas_populacao].astype(int)

    # Separa a coluna 'municipio' em 'municipio' e 'uf'
    df_final[['municipio', 'uf']] = df_final['municipio'].str.split(' - ', n=1, expand=True)
    df_final['municipio'] = df_final['municipio'].str.strip()
    df_final['uf'] = df_final['uf'].str.strip()

    colunas_populacao = df_final.columns.drop(['municipio', 'uf'])
    # Garante que todas as colunas de população sejam do tipo inteiro
    colunas_populacao = [group['coluna'] for group in groups_data]
    df_final[colunas_populacao] = df_final[colunas_populacao].astype(int)
    
    # Calcula a população total
    df_final['pop_total'] = df_final[colunas_populacao].sum(axis=1)

    # Reorganiza as colunas para um formato final e lógico
    ordem_colunas = ['municipio', 'uf'] + [col for col in df_final if col not in ['municipio', 'uf']]
    df_final = df_final[ordem_colunas]

    df_final.dropna(subset=['uf'], inplace=True)
    
    print("--- Processamento de dados concluído com sucesso! ---")
    return df_final