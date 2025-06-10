import re
import csv

def limpar_municipio_avancado(texto_bruto, uf):
    """
    Função avançada e otimizada para extrair o nome do município de uma string complexa.
    """
    # Inicia com o texto, convertendo para maiúsculas para padronizar
    nome = texto_bruto.strip().upper()

    # Etapas 1 e 2: Remoção de sufixos e da UF (seu código original, está ótimo)
    nome = re.sub(r'\s*\([^)]*\)$', '', nome)
    nome = re.sub(r'\s+-\s+[A-Z0-9]+$', '', nome)
    nome = re.split(r'\s*-\s*' + re.escape(uf) + r'\s*$', nome, flags=re.IGNORECASE)[0]
    nome = re.split(r'\s*/\s*' + re.escape(uf) + r'\s*$', nome, flags=re.IGNORECASE)[0]

    # --- AJUSTE PRINCIPAL (ETAPA 3) ---
    # Unimos todos os termos-pivô em uma única expressão regular para mais eficiência.
    # Também ajustamos para lidar com variações de acentos e espaços.
    termos_pivo = [
        r"Do\s+Munic[ií]pio\s+De",
        r"Municipais\s+De",
        r"Municipalidade\s+De",
        r"Esgoto\s+De",
        r"[AÁ]gua\s+De",
        r"Tur[ií]stica\s+De",
        r"Ambiental\s+De",
        r"Urbanismo\s+De",
        r"Prefeitura\s+De",
        r"Vereadores\s+De",
        r"Sa[uú]de\s+De",
        r"Servidores\s+De",
        r"Municip[aá]rios\s+De",
        r"Social\s+De",
        r"P[uú]blicos\s+De",
        r"Samae\s+-+\s+De",
        r"Munic[ií]pio\s+De",
        r"Previd[eê]ncia\s+De",
        r"C[aâ]mara\s+De",
        r"De\s+Previd[eê]ncia",
        r"Sa[uú]de\s+De",
        r"Social\s+De",
        r"C[aâ]mara\s+Municipal\s+De",
        r"P[uú]blicos\s+De",
        r"Municipais\s+De",
        r"Municip[aá]rios\s+De",
        r"Prefeitura\s+De",
        r"Mun\.\s+De",
        r"Municipal\s+De",
        r"\s+Munic[ií]pio",
        r"Previd[eê]ncia"
    ]
    
    # Cria o padrão final unindo os termos com `|` (OU)
    # A estrutura (?:...) é um "grupo sem captura", usado aqui para agrupar os termos.
    padrao_pivo_unificado = r"^(?:.*)(" + "|".join(termos_pivo) + r")"

    # Aplica a substituição uma única vez.
    # Esta expressão remove tudo desde o início da linha até o final do termo-pivô encontrado.
    nome = re.sub(padrao_pivo_unificado, '', nome, flags=re.IGNORECASE)

    # Etapa 4: Remove sufixos comuns (seu código original)
    nome = re.sub(r'\s*PREV[A-Z]*$', '', nome, flags=re.IGNORECASE)
    nome = re.sub(r'\s*IPREV$', '', nome, flags=re.IGNORECASE)

    # Etapa 5: Lida com casos como "Joinville e IPREVILLE" (seu código original)
    partes = re.split(r'\s+E\s+', nome)
    if len(partes) > 1 and partes[-1].isupper() and len(partes[-1]) > 2:
        nome = ' E '.join(partes[:-1])

    # Etapa 6: Limpeza final (seu código original)
    nome = re.sub(r'\s+', ' ', nome).strip(' .-/')
    
    # Capitaliza o nome de forma mais legível (Ex: Sao Paulo -> São Paulo)
    return nome.title()


# O restante do seu script para ler e escrever o arquivo está perfeito e não precisa de alterações.
# Apenas certifique-se de que ele chame a nova versão da função `limpar_municipio_avancado`.
def tratar_arquivo_final(arquivo_entrada='MunipCOn_tratado.csv', arquivo_saida='MunipCOn_finalv4.csv'):
    """
    Lê o arquivo CSV tratado e aplica a limpeza avançada na coluna de municípios.
    """
    try:
        with open(arquivo_entrada, mode='r', encoding='utf-8') as f_in:
            leitor = csv.DictReader(f_in, delimiter=';')
            linhas = list(leitor)
    except FileNotFoundError:
        print(f"Erro: Arquivo de entrada '{arquivo_entrada}' não encontrado.")
        return

    registros_finais = []
    for linha in linhas:
        uf = linha.get('UF', '')
        municipio_bruto = linha.get('MUNICIPIO', '')
        municipio_limpo = limpar_municipio_avancado(municipio_bruto, uf)
        linha['MUNICIPIO'] = municipio_limpo
        registros_finais.append(linha)

    if registros_finais:
        try:
            with open(arquivo_saida, mode='w', encoding='utf-8', newline='') as f_out:
                campos = registros_finais[0].keys()
                escritor = csv.DictWriter(f_out, fieldnames=campos, delimiter=';')
                escritor.writeheader()
                escritor.writerows(registros_finais)
            print(f"Sucesso! Dados finalizados e salvos em '{arquivo_saida}'.")
        except IOError:
            print(f"Erro: Não foi possível escrever no arquivo '{arquivo_saida}'.")


if __name__ == '__main__':
    tratar_arquivo_final()