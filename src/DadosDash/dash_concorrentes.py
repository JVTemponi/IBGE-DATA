import pandas as pd
import dash
from dash import dcc, html, Input, Output, State
import plotly.express as px
import unicodedata
import numpy as np 

MAPA_CODIGO_UF = {
    11: 'RO', 12: 'AC', 13: 'AM', 14: 'RR', 15: 'PA', 16: 'AP', 17: 'TO', 21: 'MA',
    22: 'PI', 23: 'CE', 24: 'RN', 25: 'PB', 26: 'PE', 27: 'AL', 28: 'SE', 29: 'BA',
    31: 'MG', 32: 'ES', 33: 'RJ', 35: 'SP', 41: 'PR', 42: 'SC', 43: 'RS', 50: 'MS',
    51: 'MT', 52: 'GO', 53: 'DF'
}

FAIXAS_ETARIAS_MAP = {
    'pop_0_14':     '0 a 14 anos',
    'pop_15_19':    '15 a 19 anos',
    'pop_20_29':    '20 a 29 anos',
    'pop_30_39':    '30 a 39 anos',
    'pop_40_49':    '40 a 49 anos',
    'pop_50_59':    '50 a 59 anos',
    'pop_60_74':    '60 a 74 anos',
    'pop_75_99':    '75 a 99 anos',
    'pop_100_mais': '100+ anos'
}

GEOJSON_URL = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"

COLORS = {
    'background': "#AAD3DF",
    'text': "#FFFFFF",
    'plot_background': "#AAD3DF",
    'bg-bar': "#272727",
}

# --- Funções de Preparação de Dados ---
def carregar_dados_csv():
    try:
        df_municipios = pd.read_csv('municipios.csv')
        df_empresas = pd.read_csv('empresas.csv', sep=';')
        df_estados = pd.read_csv('estados.csv')
        df_pop_raw = pd.read_csv('populacao_ibge.csv', sep=';')
        return df_municipios, df_empresas, df_estados, df_pop_raw
    except FileNotFoundError as e:
        print(f"ERRO: Arquivo não encontrado. {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# def carregar_dados_db():
#     try:
#         con = 'BD'
#         df_municipios = pd.read_sql('SELECT * FROM municipios', con)
#         df_empresas = pd.read_sql('SELECT * FROM empresas', con)
#         df_estados = pd.read_sql('SELECT * FROM estados', con)
#         df_pop_raw = pd.read_sql('SELECT * FROM populacao_ibge', con)
#         con.close()
        
#         return df_municipios, df_empresas, df_estados, df_pop_raw
#     except Exception as e:
#         print(f"ERRO: Falha ao conectar ou ler o banco de dados. {e}")
#         return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

def normalizar_texto(texto):
    """
    Normaliza uma string: remove acentos, converte para minúsculas e remove espaços extras.
    """
    if not isinstance(texto, str):
        return texto
    texto = texto.lower()
    return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn').strip()

def preparar_dados(df_municipios, df_empresas, df_estados, df_pop_raw):
    """
    Processa e integra os DataFrames brutos para gerar os dados finais para os gráficos.
    Retorna os DataFrames processados para o mapa e para os gráficos de população.
    """
    if any(df.empty for df in [df_municipios, df_empresas, df_estados, df_pop_raw]):
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    # Normalizar textos e mapear UFs
    df_municipios['uf'] = df_municipios['codigo_uf'].map(MAPA_CODIGO_UF)
    df_empresas['municipio_normalizado'] = df_empresas['municipio'].apply(normalizar_texto)
    df_municipios['nome_normalizado'] = df_municipios['nome'].apply(normalizar_texto)

    # Preparar dados de população por ESTADO
    df_pop_estado = df_pop_raw.groupby('uf').sum(numeric_only=True)
    df_pop_final_estado = df_pop_estado[list(FAIXAS_ETARIAS_MAP.keys())].reset_index()
    df_pop_plot_estado = df_pop_final_estado.melt(id_vars='uf', var_name='faixa_etaria', value_name='populacao')
    df_pop_plot_estado['faixa_etaria'] = df_pop_plot_estado['faixa_etaria'].replace(FAIXAS_ETARIAS_MAP)

    # Preparar dados de população por MUNICÍPIO
    df_pop_municipio = df_pop_raw.copy()
    df_pop_municipio['municipio_normalizado'] = df_pop_municipio['municipio'].apply(normalizar_texto)
    df_pop_municipio = pd.merge(
        df_pop_municipio,
        df_municipios[['codigo_ibge', 'nome_normalizado', 'uf']],
        left_on=['municipio_normalizado', 'uf'],
        right_on=['nome_normalizado', 'uf'],
        how='left'
    )
    colunas_pop_melt = ['codigo_ibge', 'municipio', 'pop_total'] + list(FAIXAS_ETARIAS_MAP.keys())
    df_pop_plot_municipio = df_pop_municipio[colunas_pop_melt].melt(
        id_vars=['codigo_ibge', 'municipio'], var_name='faixa_etaria', value_name='populacao'
    )
    df_pop_plot_municipio['faixa_etaria'] = df_pop_plot_municipio['faixa_etaria'].replace(FAIXAS_ETARIAS_MAP)

    # Criar DataFrame principal para o mapa
    df_mapa = pd.merge(
        df_empresas,
        df_municipios,
        left_on=['municipio_normalizado', 'uf'],
        right_on=['nome_normalizado', 'uf'],
        how='left'
    )
    df_mapa.dropna(subset=['latitude', 'longitude', 'uf', 'codigo_ibge'], inplace=True)

    return df_mapa, df_pop_plot_estado, df_pop_plot_municipio, df_estados

# --- Carregamento e Preparação Inicial ---
df_municipios_raw, df_empresas_raw, df_estados_raw, df_pop_raw = carregar_dados_csv()
# df_municipios_raw, df_empresas_raw, df_estados_raw, df_pop_raw = carregar_dados_db() # Exemplo

df_mapa, df_pop_plot_estado, df_pop_plot_municipio, df_estados = preparar_dados(
    df_municipios_raw, df_empresas_raw, df_estados_raw, df_pop_raw
)

# --- Inicialização do App Dash ---
app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server # Expor o servidor para a publicação (deploy)
app.title = 'Distribuição de Concorrentes'


# --- Funções de Criação de Layout ---
def criar_layout_principal():
    """Cria o layout da página principal com o mapa e os filtros."""
    return html.Div(style={'backgroundColor': COLORS['background'], 'fontFamily': 'Arial, sans-serif', 'margin':'0px auto'}, children=[
        html.H1('Distribuição de Concorrentes', style={'textAlign': 'center', 'color': COLORS['text'], 'margin':'0px auto'}),
        html.Div([
            html.Button("Baixar Dados (CSV)", id="btn_download_csv", style={'marginRight': '15px'}),
            dcc.Download(id="download-dataframe-csv"),
        ], style={'textAlign': 'center', 'padding': '10px'}),

        html.Div([
            dcc.Dropdown(id='filtro-estado', options=[{'label': nome, 'value': uf} for uf, nome in df_estados.sort_values('nome').set_index('uf')['nome'].items()] if not df_estados.empty else [], placeholder='Filtrar por Estado (UF)', multi=True),
            dcc.Dropdown(id='filtro-tipo', options=[{'label': tipo, 'value': tipo} for tipo in sorted(df_mapa['tipo_estabelecimento'].dropna().unique())] if not df_mapa.empty else [], placeholder='Filtrar por Tipo', multi=True),
            dcc.Dropdown(id='filtro-concorrente', options=[{'label': concorrente, 'value': concorrente} for concorrente in sorted(df_mapa['concorrente'].dropna().unique())] if not df_mapa.empty else [], placeholder='Filtrar por Concorrente', multi=True),
            dcc.Dropdown(id='filtro-status', options=[{'label': status, 'value': status} for status in sorted(df_mapa['status'].dropna().unique())] if not df_mapa.empty else [], placeholder='Filtrar por Status', multi=True)
        ], style={'width': '40%', 'margin': '0px auto', 'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '10px'}),
        dcc.RadioItems(
            id='seletor-mapa',
            options=[{'label': 'Cidades', 'value': 'scatter'}, {'label': 'Estados', 'value': 'choropleth'}],
            value='scatter',
            labelStyle={'display': 'inline-block', 'marginRight': '10px', 'color': COLORS['text']},
            style={'textAlign': 'center', 'margin': '10px'}
        ),
        dcc.Graph(id='mapa-clientes', style={'height': '90vh'}, config={'displayModeBar': False, 'scrollZoom': True, 'displaylogo': False}),
    ])

def criar_layout_detalhes_estado(estado_selecionado):
    """Cria o layout da página de detalhes demográficos para um estado."""
    if df_pop_plot_estado.empty or estado_selecionado not in df_pop_plot_estado['uf'].unique():
        return html.Div([html.H1("Dados não encontrados.", style={'color': COLORS['text']}), dcc.Link('Voltar ao Mapa', href='/', style={'color': '#7FDBFF'})])
    
    df_filtrado = df_pop_plot_estado[df_pop_plot_estado['uf'] == estado_selecionado]
    nome_estado = df_estados[df_estados['uf'] == estado_selecionado]['nome'].iloc[0]
    
    fig = px.bar(
        df_filtrado, 
        x='faixa_etaria', 
        y='populacao',
        title=f'População por Faixa Etária - {nome_estado}',
        labels={'faixa_etaria': 'Faixa Etária', 'populacao': 'População'},
        text='populacao',
        template='plotly_dark'
    )
    
    fig.update_traces(
        texttemplate='%{text:,.0f}', 
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>População: %{y:,.0f}<extra></extra>',
        marker=dict(
            color='#4682B4', 
            cornerradius=8
        )
    )
    
    fig.update_layout(
        title_x=0.5,
        xaxis_title=None,
        yaxis_title="População",
        uniformtext_minsize=8, 
        uniformtext_mode='hide',
        yaxis=dict(showgrid=False),
        plot_bgcolor=COLORS['bg-bar'],
        paper_bgcolor=COLORS['bg-bar']
    )
    
    max_pop = df_filtrado['populacao'].max()
    fig.update_yaxes(range=[0, max_pop * 1.15])
    
    return html.Div(style={'backgroundColor': COLORS['bg-bar'], 'padding': '20px','margin': '0px' ,'minHeight': '100vh'}, children=[
        html.H1(f'Detalhes Demográficos: {nome_estado}', style={'textAlign': 'center', 'color': COLORS['text']}),
        dcc.Graph(figure=fig),
        dcc.Link('<< Voltar ao Mapa', href='/', style={'textAlign': 'center', 'display': 'block', 'fontSize': '20px', 'color': '#7FDBFF'})
    ])

def criar_layout_detalhes_cidade(nome_mun):
    """Cria o layout da página de detalhes demográficos para uma cidade."""
    if df_pop_plot_municipio.empty or nome_mun not in df_pop_plot_municipio['municipio'].unique():
        return html.Div([html.H1("Dados não encontrados.", style={'color': COLORS['text']}), dcc.Link('Voltar ao Mapa', href='/', style={'color': '#7FDBFF'})])

    pop_total = df_pop_plot_municipio[
        (df_pop_plot_municipio['municipio'] == nome_mun) &
        (df_pop_plot_municipio['faixa_etaria'] == 'pop_total')
    ]['populacao'].iloc[0]

    df_filtrado = df_pop_plot_municipio[
        (df_pop_plot_municipio['municipio'] == nome_mun) &
        (df_pop_plot_municipio['faixa_etaria'] != 'pop_total')
    ]

    fig = px.bar(
        df_filtrado, 
        x='faixa_etaria', 
        y='populacao',
        title=f'População por Faixa Etária - {nome_mun}<br><b>Total de {pop_total:,.0f} Habitantes</b>'.replace(',', '.'),
        labels={'faixa_etaria': 'Faixa Etária', 'populacao': 'População'},
        text='populacao',
        template='plotly_dark'
    )

    fig.update_traces(
        texttemplate='%{text:,.0f}', 
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>População: %{y:,.0f}<extra></extra>',
        marker=dict(
            color='#4682B4',
            cornerradius=8
        )
    )

    fig.update_layout(
        title_x=0.5,
        xaxis_title=None,
        yaxis_title="População",
        uniformtext_minsize=8, 
        uniformtext_mode='hide',
        yaxis=dict(showgrid=False),
        plot_bgcolor=COLORS['bg-bar'],
        paper_bgcolor=COLORS['bg-bar'],
        title_font_size=20
    )
    
    max_pop = df_filtrado['populacao'].max()
    fig.update_yaxes(range=[0, max_pop * 1.15])

    return html.Div(style={'backgroundColor': COLORS['bg-bar'], 'padding': '10px', 'minHeight': '150vh'}, children=[
        html.H1(f'{nome_mun}', style={'textAlign': 'center', 'color': COLORS['text']}),
        dcc.Graph(figure=fig),
        dcc.Link('<< Voltar ao Mapa', href='/', style={'textAlign': 'center', 'display': 'block', 'fontSize': '15px', 'color': "#18BEFF"})
    ])

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])


# --- Callbacks ---
@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname):
    if pathname and pathname.startswith('/detalhes-estado/'):
        return criar_layout_detalhes_estado(pathname.split('/')[-1])
    if pathname and pathname.startswith('/detalhes-cidade/'):
        return criar_layout_detalhes_cidade(pathname.split('/')[-1])
    return criar_layout_principal()

@app.callback(
    Output('mapa-clientes', 'figure'),
    [Input('filtro-estado', 'value'), Input('filtro-tipo', 'value'),
     Input('filtro-concorrente', 'value'), Input('filtro-status', 'value'),
     Input('seletor-mapa', 'value')]
)
def update_map_figure(estados, tipos, concorrentes, status, tipo_mapa):
    """Atualiza a figura do mapa com base nos filtros selecionados."""
    df_filtrado = df_mapa.copy()
    if estados: df_filtrado = df_filtrado[df_filtrado['uf'].isin(estados)]
    if tipos: df_filtrado = df_filtrado[df_filtrado['tipo_estabelecimento'].isin(tipos)]
    if concorrentes: df_filtrado = df_filtrado[df_filtrado['concorrente'].isin(concorrentes)]
    if status: df_filtrado = df_filtrado[df_filtrado['status'].isin(status)]

    if df_filtrado.empty:
        return {"layout": {"paper_bgcolor": COLORS['plot_background'], "plot_bgcolor": COLORS['plot_background'], "font": {"color": COLORS['text']}, "annotations": [{"text": "Nenhum dado para os filtros", "xref": "paper", "yref": "paper", "showarrow": False}]}}

    if tipo_mapa == 'scatter':
        df_scatter = df_filtrado.copy()
        jitter_amount = 0.040
        is_duplicated = df_scatter.duplicated(subset=['latitude', 'longitude'], keep=False)
        num_duplicates = is_duplicated.sum()
        if num_duplicates > 0:
            df_scatter.loc[is_duplicated, 'latitude'] += np.random.uniform(-jitter_amount, jitter_amount, size=num_duplicates)
            df_scatter.loc[is_duplicated, 'longitude'] += np.random.uniform(-jitter_amount, jitter_amount, size=num_duplicates)
        
        fig = px.scatter_mapbox(
            df_scatter,
            lat="latitude", lon="longitude", color="concorrente",
            zoom=3.8, center={"lat": -14.2350, "lon": -51.9253},
            mapbox_style="open-street-map",
            hover_name="municipio", custom_data=['municipio']
        )
        fig.update_traces(
            marker=dict(
                size=7.5,
                opacity=1.0
            )
        )
        fig.update_layout(
            margin={"r":0, "t":0, "l":0, "b":0},
            legend=dict(
                title_text='Concorrentes',
                bgcolor="rgba(255, 255, 255, 0.8)", 
                borderwidth=1,
                y=1, yanchor="top",
                x=1, xanchor="right"
            )
        )

    else: 
        df_agregado = df_filtrado.groupby('uf').size().reset_index(name='contagem')
        fig = px.choropleth_mapbox(
            df_agregado, geojson=GEOJSON_URL, locations='uf', featureidkey="properties.sigla",
            color='contagem', color_continuous_scale="YlOrRd",
            #mapbox_style="carto-positron", 
            mapbox_style="open-street-map",
            zoom=3.5,
            center={"lat": -14.2350, "lon": -51.9253}, opacity=0.9
        )
        fig.update_layout(
            margin={"r":0, "t":0, "l":0, "b":0},
            paper_bgcolor=COLORS['plot_background'],
            plot_bgcolor=COLORS['plot_background'],
            font_color=COLORS['text'],
            coloraxis_colorbar_title_text='Nº de Licitações',
        )
    return fig


@app.callback(
    Output('url', 'pathname'),
    Input('mapa-clientes', 'clickData'),
    State('seletor-mapa', 'value'),
    prevent_initial_call=True
)
def navigate_on_click(clickData, tipo_mapa):
    if not clickData: return dash.no_update
    if tipo_mapa == 'choropleth': return f'/detalhes-estado/{clickData["points"][0]["location"]}'
    if tipo_mapa == 'scatter': return f'/detalhes-cidade/{clickData["points"][0]["customdata"][0]}'
    return dash.no_update

@app.callback(
    Output("download-dataframe-csv", "data"),
    Input("btn_download_csv", "n_clicks"),
    prevent_initial_call=True,
)
def download_csv(n_clicks):
    return dict(content=df_empresas_raw.to_csv(sep=';', index=False, encoding='utf-8'), filename="dados_empresas.csv")



if __name__ == '__main__':
    app.run(debug=True)
