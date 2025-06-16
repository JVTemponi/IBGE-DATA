import re
import csv
from datetime import datetime

def tratar_dados_municipais(arquivo_entrada='MunipCOn.txt', arquivo_saida='MunipCOn_tratado.csv'):
    """
    Lê, trata e salva os dados de contratos municipais a partir de um arquivo de texto.

    As seguintes tratativas são realizadas:
    - A coluna 'ID_JIRA' é removida.
    - O campo 'MUNICIPIO' é limpo para conter apenas o nome da cidade.
    - As datas são convertidas do formato 'dd/mm/yyyy' para 'YYYY-MM-DD'.
    - Lida com linhas quebradas e malformadas no arquivo de origem.
    """
    try:
        with open(arquivo_entrada, 'r', encoding='utf-8') as f:
            conteudo_bruto = f.read()
    except FileNotFoundError:
        print(f"Erro: O arquivo '{arquivo_entrada}' não foi encontrado.")
        print("Por favor, certifique-se de que o script e o arquivo de dados estejam na mesma pasta.")
        return

    # Limpeza preliminar do conteúdo para facilitar a análise
    # Remove as tags de fonte, ex: 
    conteudo_limpo = re.sub(r'\\', '', conteudo_bruto)
    
    # Junta linhas que foram quebradas incorretamente no meio de um registro
    # A lógica assume que uma linha válida termina com uma data no formato dd/mm/yyyy
    conteudo_limpo = re.sub(r'(?<!\d{4})\n(?![A-Z]{3}-\d+;)', ' ', conteudo_limpo)

    # Define o cabeçalho para o novo arquivo CSV
    cabecalho_saida = [
        "CHAMADO", "UF", "MUNICIPIO", "TIPO_ETABELECIMENTO",
        "CONCORRENTE", "STATUS", "DATA_INI", "DATA_FIM"
    ]
    
    registros_tratados = [cabecalho_saida]
    
    # Lê as linhas tratadas usando o módulo CSV do Python
    linhas = conteudo_limpo.strip().split('\n')
    leitor_csv = csv.reader(linhas[1:], delimiter=';') # Pula o cabeçalho original

    for linha in leitor_csv:
        if len(linha) != 9:
            continue # Ignora linhas que não tenham 9 colunas

        # Extrai os dados da linha
        chamado, _, uf, municipio_raw, tipo_estab, concorrente, status, data_ini, data_fim = linha

        # --- Tratativa 1: Limpeza do nome do Município ---
        # Remove a sigla do estado (UF) e outros ruídos do final do nome
        municipio_limpo = re.split(r'\s*-\s*[A-Z]{2}\s*$|\s*/\s*[A-Z]{2}\s*$', municipio_raw.strip())[0]
        # Remove prefixos comuns e ajusta espaçamentos
        municipio_limpo = re.sub(r"^(MUNICÍPIO DE|: MUNICÍPIO DE)\s*", "", municipio_limpo, flags=re.IGNORECASE).strip()

        # --- Tratativa 2: Formatação das Datas ---
        def formatar_data(data_str):
            try:
                return datetime.strptime(data_str.strip(), '%d/%m/%Y').strftime('%Y-%m-%d')
            except ValueError:
                return data_str.strip() # Retorna o valor original se o formato for inválido

        data_ini_formatada = formatar_data(data_ini)
        data_fim_formatada = formatar_data(data_fim)

        # --- Montagem da nova linha (sem a coluna ID_JIRA) ---
        registros_tratados.append([
            chamado.strip(),
            uf.strip(),
            municipio_limpo,
            tipo_estab.strip(),
            concorrente.strip(),
            status.strip(),
            data_ini_formatada,
            data_fim_formatada
        ])

    # --- Geração do novo arquivo CSV ---
    try:
        with open(arquivo_saida, 'w', newline='', encoding='utf-8') as f:
            escritor_csv = csv.writer(f, delimiter=';')
            escritor_csv.writerows(registros_tratados)
        print(f"Sucesso! Os dados foram tratados e salvos em '{arquivo_saida}'.")
    except IOError:
        print(f"Erro: Não foi possível escrever no arquivo '{arquivo_saida}'.")

# --- Execução da Função ---
if __name__ == '__main__':
    tratar_dados_municipais()