# config.py
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'name': os.getenv('DB_NAME')
}
DB_TABLE_NAME = 'bi_populacao_por_faixa_etaria'


# Faixa estária dos grupos IBGE
FAIXAS_ETARIAS = [
    {'cod': '93070,93084,93085', 'coluna': 'pop_0_14'}, # população de 0 a 14 anos
    {'cod': '93086', 'coluna': 'pop_15_19'}, # população de 15 a 19 anos
    {'cod': '93087,93088', 'coluna': 'pop_20_29'}, # população de 20 a 29 anos
    {'cod': '93089,93090', 'coluna': 'pop_30_39'}, # população de 30 a 39 anos
    {'cod': '93091,93092', 'coluna': 'pop_40_49'}, # população de 40 a 49 anos
    {'cod': '93093,93094', 'coluna': 'pop_50_59'}, # população de 50 a 59 anos
    {'cod': '93095,93096,93097', 'coluna': 'pop_60_74'}, # população de 60 a 74 anos
    {'cod': '93098,49108,49109,60040,60041', 'coluna': 'pop_75_99'}, # população de 75 a 99 anos
    {'cod': '6653', 'coluna': 'pop_100_mais'} # populacao mais de 100 anos
]

SIDRA_API_POP = {
    'table_code': '9514',
    'territorial_level': '6',
    'variable': '93',
    'ibge_territorial_code': 'all',
    'classifications': {'2': '6794'} # Sexo: Total
}

QUERY_CIDADES_MG = """
    select * 
    from bi_populacao_por_faixa_etaria 
    where 1=1
        and uf = 'MG' 
    and municipio in ('Belo Horizonte','Congonhas','Ouro Branco','Rio Pomba','Santa Maria do Suaçuí')
    order by pop_total desc;
"""