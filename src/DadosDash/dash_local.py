import pandas as pd
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import unicodedata

# --- 1. Carregamento e Preparação dos Dados ---
try:
    df_municipios = pd.read_csv('municipios.csv')
    df_empresas = pd.read_csv('empresas.csv', sep=';')
    df_estados = pd.read_csv('estados.csv')
except FileNotFoundError as e:
    print(f"Erro: Arquivo não encontrado.{e}")

# --- 2. Limpeza e Junção dos Dados ---

print("Verificando e corrigindo coordenadas para o território brasileiro...")

def corrigir_latitude(lat):
    if pd.isna(lat): return None
    if -34 <= lat <= 6: return lat
    temp_lat = float(lat)
    for _ in range(5):
        temp_lat /= 10
        if -34 <= temp_lat <= 6: return temp_lat
    return None

def corrigir_longitude(lon):
    if pd.isna(lon): return None
    if -74 <= lon <= -34: return lon
    temp_lon = float(lon)
    for _ in range(5):
        temp_lon /= 10
        if -74 <= temp_lon <= -34: return temp_lon
    return None

df_municipios['latitude'] = df_municipios['latitude'].apply(corrigir_latitude)
df_municipios['longitude'] = df_municipios['longitude'].apply(corrigir_longitude)

mapa_codigo_uf = {
    11: 'RO', 12: 'AC', 13: 'AM', 14: 'RR', 15: 'PA', 16: 'AP', 17: 'TO', 21: 'MA',
    22: 'PI', 23: 'CE', 24: 'RN', 25: 'PB', 26: 'PE', 27: 'AL', 28: 'SE', 29: 'BA',
    31: 'MG', 32: 'ES', 33: 'RJ', 35: 'SP', 41: 'PR', 42: 'SC', 43: 'RS', 50: 'MS',
    51: 'MT', 52: 'GO', 53: 'DF'
}
df_municipios['uf'] = df_municipios['codigo_uf'].map(mapa_codigo_uf)

def normalizar_texto(texto):
    if not isinstance(texto, str): return texto
    texto = texto.lower()
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    return texto.strip()

df_empresas['municipio_normalizado'] = df_empresas['municipio'].apply(normalizar_texto)
df_municipios['nome_normalizado'] = df_municipios['nome'].apply(normalizar_texto)

df_mapa = pd.merge(
    df_empresas,
    df_municipios,
    left_on=['municipio_normalizado', 'uf'],
    right_on=['nome_normalizado', 'uf'],
    how='left'
)

df_mapa.dropna(subset=['latitude', 'longitude', 'uf'], inplace=True)


# --- 3. Criação do App Dash ---
app = dash.Dash(__name__)
app.title = 'Dashboard - Distribuição de Concorrentes'

# URL para o arquivo GeoJSON com as fronteiras dos estados do Brasil
geojson_url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"

app.layout = html.Div(style={'backgroundColor': "#D1C5C5", 'fontFamily': 'Arial, sans-serif'}, children=[
    html.H1(
        children='Dashboard - Distribuição de Concorrentes',
        style={'textAlign': 'center', 'color': '#333'}
    ),
    html.P(
        'Use os filtros abaixo e escolha o tipo de mapa para explorar os dados.',
        style={'textAlign': 'center', 'color': '#555'}
    ),
    html.Div([
        dcc.Dropdown(id='filtro-estado', options=[{'label': nome, 'value': uf} for uf, nome in df_estados.sort_values('nome').set_index('uf')['nome'].items()], placeholder='Filtrar por Estado (UF)', multi=True),
        dcc.Dropdown(id='filtro-tipo', options=[{'label': tipo, 'value': tipo} for tipo in sorted(df_mapa['tipo_estabelecimento'].dropna().unique())], placeholder='Filtrar por Tipo de Estabelecimento', multi=True),
        dcc.Dropdown(id='filtro-concorrente', options=[{'label': concorrente, 'value': concorrente} for concorrente in sorted(df_mapa['concorrente'].dropna().unique())], placeholder='Filtrar por Concorrente', multi=True),
        dcc.Dropdown(id='filtro-status', options=[{'label': status, 'value': status} for status in sorted(df_mapa['status'].dropna().unique())], placeholder='Filtrar por Status', multi=True)
    ], style={'width': '30%', 'margin': '20px auto', 'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '10px'}),
    
    # NOVO: Seletor de tipo de mapa
    dcc.RadioItems(
        id='seletor-mapa',
        options=[
            {'label': 'Mapa de Pontos', 'value': 'scatter'},
            {'label': 'Mapa de Calor', 'value': 'choropleth'},
        ],
        value='scatter', # Valor inicial
        labelStyle={'display': 'inline-block', 'marginRight': '20px'},
        style={'textAlign': 'center', 'margin': '20px'}
    ),
    
    dcc.Graph(id='mapa-clientes', style={'height': '70vh'})
])

# --- 4. Callback para Interatividade ---
@app.callback(
    Output('mapa-clientes', 'figure'),
    [Input('filtro-estado', 'value'), Input('filtro-tipo', 'value'),
     Input('filtro-concorrente', 'value'), Input('filtro-status', 'value'),
     Input('seletor-mapa', 'value')] # Novo input
)
def update_map(estados, tipos, concorrentes, status, tipo_mapa):
    df_filtrado = df_mapa.copy()

    # Lógica de filtro robusta
    if estados: df_filtrado = df_filtrado[df_filtrado['uf'].isin(estados)]
    if tipos: df_filtrado = df_filtrado[df_filtrado['tipo_estabelecimento'].isin(tipos)]
    if concorrentes: df_filtrado = df_filtrado[df_filtrado['concorrente'].isin(concorrentes)]
    if status: df_filtrado = df_filtrado[df_filtrado['status'].isin(status)]

    if df_filtrado.empty:
        return {"layout": {"annotations": [{"text": "Nenhum dado para os filtros selecionados", "xref": "paper", "yref": "paper", "showarrow": False, "font": {"size": 20}}]}}

    # Lógica para escolher qual mapa desenhar
    if tipo_mapa == 'scatter':
        fig = px.scatter_mapbox(
            df_filtrado, lat="latitude", lon="longitude", color="concorrente",
            size_max=15, zoom=3.5, center={"lat": -14.2350, "lon": -51.9253},
            mapbox_style="carto-positron", hover_name="municipio",
            hover_data={"tipo_estabelecimento": True, "concorrente": True, "status": True, "latitude": False, "longitude": False},
            title='Distribuição de Clientes por Localização (Pontos)'
        )
    else: # tipo_mapa == 'choropleth'
        # Agrega os dados por estado para contar o número de clientes
        df_agregado = df_filtrado.groupby('uf').size().reset_index(name='contagem')
        
        fig = px.choropleth_mapbox(
            df_agregado,
            geojson=geojson_url,
            locations='uf', # Coluna do dataframe que corresponde à sigla no GeoJSON
            featureidkey="properties.sigla", # Caminho para a sigla do estado dentro do GeoJSON
            color='contagem', # Coluna que definirá a cor
            color_continuous_scale="Blues", # Esquema de cores (azul para vermelho)
            mapbox_style="carto-positron",
            zoom=3.5,
            center={"lat": -14.2350, "lon": -51.9253},
            opacity=0.7,
            hover_name='uf',
            hover_data={'contagem': True},
            title='Densidade de Clientes por Estado (Mapa de Calor)'
        )
        fig.update_layout(coloraxis_colorbar_title_text = 'Nº de Clientes')


    fig.update_layout(margin={"r":0,"t":40,"l":0,"b":0}, legend_title_text='Concorrentes')
    return fig

# --- 5. Executar o Servidor ---
if __name__ == '__main__':
    app.run(debug=True)
