import pandas as pd
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import unicodedata

try:
    df_municipios = pd.read_csv('municipios.csv')
    df_empresas = pd.read_csv('empresas.csv', sep=';')
    df_estados = pd.read_csv('estados.csv')
except FileNotFoundError as e:
    print(f"Erro: Arquivo não encontrado. {e}")

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

app = dash.Dash(__name__)
app.title = 'Dashboard Concorrentes Brasil'

app.layout = html.Div(style={'backgroundColor': '#f0f0f0', 'fontFamily': 'Arial, sans-serif'}, children=[
    html.H1(
        children='Dashboard - Distribuição de Concorrentes',
        style={'textAlign': 'center'}
    ),
    html.Div([
        dcc.Dropdown(id='filtro-estado', options=[{'label': nome, 'value': uf} for uf, nome in df_estados.sort_values('nome').set_index('uf')['nome'].items()], placeholder='Estado (UF)', multi=True),
        dcc.Dropdown(id='filtro-tipo', options=[{'label': tipo, 'value': tipo} for tipo in sorted(df_mapa['tipo_estabelecimento'].dropna().unique())], placeholder='Tipo de Estabelecimento', multi=True),
        dcc.Dropdown(id='filtro-concorrente', options=[{'label': concorrente, 'value': concorrente} for concorrente in sorted(df_mapa['concorrente'].dropna().unique())], placeholder='Concorrente', multi=True),
        dcc.Dropdown(id='filtro-status', options=[{'label': status, 'value': status} for status in sorted(df_mapa['status'].dropna().unique())], placeholder='Status do Contrato', multi=True)
    ], style={'width': '50%', 'margin': '20px auto', 'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '10px'}),

    dcc.RadioItems(
        id='seletor-mapa',
        options=[
            {'label': 'Pontos', 'value': 'scatter'},
            {'label': 'Mapa de Densidade', 'value': 'density'}, # ALTERADO
        ],
        value='scatter',
        labelStyle={'display': 'inline-block', 'marginRight': '10px'},
        style={'textAlign': 'center', 'margin': '30px'}
    ),
    
    dcc.Graph(id='mapa-concorrentes', style={'height': '70vh'})
])

@app.callback(
    Output('mapa-concorrentes', 'figure'),
    [
        Input('filtro-estado', 'value'), 
        Input('filtro-tipo', 'value'),
        Input('filtro-concorrente', 'value'), 
        Input('filtro-status', 'value'),
        Input('seletor-mapa', 'value')
    ]
)
def update_map(estados, tipos, concorrentes, status, tipo_mapa):
    df_filtrado = df_mapa.copy()

    if estados: df_filtrado = df_filtrado[df_filtrado['uf'].isin(estados)]
    if tipos: df_filtrado = df_filtrado[df_filtrado['tipo_estabelecimento'].isin(tipos)]
    if concorrentes: df_filtrado = df_filtrado[df_filtrado['concorrente'].isin(concorrentes)]
    if status: df_filtrado = df_filtrado[df_filtrado['status'].isin(status)]

    if df_filtrado.empty:
        return {"layout": {"annotations": [{"text": "Nenhum dado para os filtros selecionados", "xref": "paper", "yref": "paper", "showarrow": False, "font": {"size": 20}}]}}

    if tipo_mapa == 'scatter':
        fig = px.scatter_mapbox(
            df_filtrado, lat="latitude", lon="longitude", color="concorrente",
            size_max=15, zoom=3.5, center={"lat": -14.2350, "lon": -51.9253},
            mapbox_style="carto-positron", hover_name="municipio",
            hover_data={"tipo_estabelecimento": True, "concorrente": True, "status": True, "latitude": False, "longitude": False},
            title='Distribuição de Concorrentes por Localização'
        )
    else: # tipo_mapa == 'density'
        fig = px.density_mapbox(
            df_filtrado,
            lat='latitude',
            lon='longitude',
            radius=5, 
            mapbox_style="carto-positron",
            hover_data={"concorrente": True, "municipio":True, "latitude": False, "longitude": False},
            opacity=0.6,
            zoom=3.0,
            center={"lat": -14.2350, "lon": -51.9253},
            title='Densidade de Concorrentes por Região'
        )

    fig.update_layout(margin={"r":0,"t":40,"l":0,"b":0}, legend_title_text='Concorrentes')
    return fig

# --- 5. Executar o Servidor ---
if __name__ == '__main__':
    app.run(debug=True)
