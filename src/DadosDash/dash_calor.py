import pandas as pd
import dash
from dash import dcc, html, Input, Output, State
import plotly.express as px
import unicodedata

try:
    df_municipios = pd.read_csv('municipios.csv')
    df_empresas = pd.read_csv('empresas.csv', sep=';')
    df_estados = pd.read_csv('estados.csv')
    df_pop_raw = pd.read_csv('populacao_ibge.csv', sep=';')

except FileNotFoundError as e:
    print(f"ERRO: Arquivo não encontrado. {e}")

if not df_municipios.empty and not df_empresas.empty and not df_pop_raw.empty:
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
        return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn').strip()

    df_empresas['municipio_normalizado'] = df_empresas['municipio'].apply(normalizar_texto)
    df_municipios['nome_normalizado'] = df_municipios['nome'].apply(normalizar_texto)

    df_pop_estado = df_pop_raw.groupby('uf').sum(numeric_only=True)
    df_pop_final_estado = df_pop_estado[['pop_0_14', 'pop_15_19', 'pop_20_29', 'pop_30_39', 'pop_40_49', 'pop_50_59', 'pop_60_74', 'pop_75_99', 'pop_100_mais']].reset_index()
    df_pop_plot_estado = df_pop_final_estado.melt(id_vars='uf', var_name='faixa_etaria', value_name='populacao')

    df_pop_municipio = df_pop_raw.copy()
    df_pop_municipio['municipio_normalizado'] = df_pop_municipio['municipio'].apply(normalizar_texto)
    df_pop_municipio = pd.merge(df_pop_municipio, df_municipios[['codigo_ibge', 'nome_normalizado', 'uf']], left_on=['municipio_normalizado', 'uf'], right_on=['nome_normalizado', 'uf'], how='left')
    df_pop_plot_municipio = df_pop_municipio[['codigo_ibge', 'municipio', 'pop_0_14', 'pop_15_19', 'pop_20_29', 'pop_30_39', 'pop_40_49', 'pop_50_59', 'pop_60_74', 'pop_75_99', 'pop_100_mais']].melt(id_vars=['codigo_ibge', 'municipio'], var_name='faixa_etaria', value_name='populacao')

    df_mapa = pd.merge(
        df_empresas,
        df_municipios,
        left_on=['municipio_normalizado', 'uf'],
        right_on=['nome_normalizado', 'uf'],
        how='left'
    )
    df_mapa.dropna(subset=['latitude', 'longitude', 'uf', 'codigo_ibge'], inplace=True)

else:
    df_mapa = pd.DataFrame()
    df_pop_plot_estado = pd.DataFrame()
    df_pop_plot_municipio = pd.DataFrame()

app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = 'Distribuição de Concorrentes'

geojson_url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"

colors = {
    'background': "#262626",
    'text': '#EAEAEA',
    'plot_background': "#262626"
}

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content'),
])


layout_mapa = html.Div(style={'backgroundColor': colors['background'], 'fontFamily': 'Arial, sans-serif'}, children=[
    html.H1('Distribuição de Concorrentes', style={'textAlign': 'center', 'color': colors['text']}),
    html.Div([
        dcc.Dropdown(id='filtro-estado', options=[{'label': nome, 'value': uf} for uf, nome in df_estados.sort_values('nome').set_index('uf')['nome'].items()] if not df_estados.empty else [], placeholder='Filtrar por Estado (UF)', multi=True),
        dcc.Dropdown(id='filtro-tipo', options=[{'label': tipo, 'value': tipo} for tipo in sorted(df_mapa['tipo_estabelecimento'].dropna().unique())] if not df_mapa.empty else [], placeholder='Filtrar por Tipo de Estabelecimento', multi=True),
        dcc.Dropdown(id='filtro-concorrente', options=[{'label': concorrente, 'value': concorrente} for concorrente in sorted(df_mapa['concorrente'].dropna().unique())] if not df_mapa.empty else [], placeholder='Filtrar por Concorrente', multi=True),
        dcc.Dropdown(id='filtro-status', options=[{'label': status, 'value': status} for status in sorted(df_mapa['status'].dropna().unique())] if not df_mapa.empty else [], placeholder='Filtrar por Status', multi=True)
    ], style={'width': '40%', 'margin': '0px auto', 'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '10px'}),
    dcc.RadioItems(
        id='seletor-mapa',
        options=[
            {'label': 'Cidades', 'value': 'scatter'},
            {'label': 'Estados', 'value': 'choropleth'},
        ],
        value='scatter',
        labelStyle={'display': 'inline-block', 'marginRight': '10px', 'color': colors['text']},
        style={'textAlign': 'center', 'margin': '10px'}
    ),
    dcc.Graph(id='mapa-clientes', style={'height': '90vh', 'backgroundColor': colors['plot_background']}, config={'displayModeBar': False, 'scrollZoom': True, 'displaylogo': False}),
])

def layout_detalhes_estado(estado_selecionado):
    if df_pop_plot_estado.empty or estado_selecionado not in df_pop_plot_estado['uf'].unique():
        return  html.Div([html.H1("Dados não encontrados.", style={'color': colors['text']}), dcc.Link('Voltar ao Mapa', href='/', style={'color': '#7FDBFF'})])
    
    df_filtrado = df_pop_plot_estado[df_pop_plot_estado['uf'] == estado_selecionado]
    nome_estado = df_estados[df_estados['uf'] == estado_selecionado]['nome'].iloc[0]
    
    fig = px.bar(
        df_filtrado, x='faixa_etaria', y='populacao', 
        title=f'População por Faixa Etária - {nome_estado}', 
        labels={'faixa_etaria': 'Faixa Etária', 'populacao': 'População'}, 
        text_auto=True,
        template='plotly_dark'
    )
    fig.update_traces(texttemplate='%{y:,.0f}', textposition='outside', marker_color='#FF9900')
    
    return html.Div(style={'backgroundColor': colors['background'], 'padding': '20px', 'minHeight': '100vh'}, children=[
        html.H1(f'Detalhes Demográficos: {nome_estado}', style={'textAlign': 'center', 'color': colors['text']}),
        dcc.Graph(figure=fig),
        dcc.Link('<< Voltar ao Mapa', href='/', style={'textAlign': 'center', 'display': 'block', 'fontSize': '20px', 'color': '#7FDBFF'})
    ])

def layout_detalhes_cidade(nome_mun):
    if df_pop_plot_municipio.empty or nome_mun not in df_pop_plot_municipio['municipio'].unique():
        return html.Div([html.H1("Dados não encontrados.", style={'color': colors['text']}), dcc.Link('Voltar ao Mapa', href='/', style={'color': '#7FDBFF'})])
        
    df_filtrado = df_pop_plot_municipio[df_pop_plot_municipio['municipio'] == nome_mun]
    nome_municipio = df_filtrado['municipio'].iloc[0]
    fig = px.bar(
        df_filtrado, x='faixa_etaria', y='populacao', 
        title=f'População por Faixa Etária - {nome_municipio}', 
        labels={'faixa_etaria': 'Faixa Etária', 'populacao': 'População'}, 
        text_auto=True,
        template='plotly_dark'
    )
    fig.update_traces(texttemplate='%{y:,.0f}', textposition='outside', marker_color='#11ACD4')

    return html.Div(style={'backgroundColor': colors['background'], 'padding': '20px', 'minHeight': '100vh'}, children=[
        html.H1(f'Detalhes Demográficos: {nome_municipio}', style={'textAlign': 'center', 'color': colors['text']}),
        dcc.Graph(figure=fig),
        dcc.Link('<< Voltar ao Mapa', href='/', style={'textAlign': 'center', 'display': 'block', 'fontSize': '20px', 'color': '#7FDBFF'})
    ])

@app.callback(Output('page-content', 'children'), Input('url', 'pathname'))
def display_page(pathname):
    if pathname and pathname.startswith('/detalhes-estado/'):
        return layout_detalhes_estado(pathname.split('/')[-1])
    if pathname and pathname.startswith('/detalhes-cidade/'):
        return layout_detalhes_cidade(pathname.split('/')[-1])
    return layout_mapa

@app.callback(
    Output('mapa-clientes', 'figure'),
    [Input('filtro-estado', 'value'), Input('filtro-tipo', 'value'),
     Input('filtro-concorrente', 'value'), Input('filtro-status', 'value'),
     Input('seletor-mapa', 'value')]
)
def update_map_figure(estados, tipos, concorrentes, status, tipo_mapa):
    df_filtrado = df_mapa.copy()
    if estados: df_filtrado = df_filtrado[df_filtrado['uf'].isin(estados)]
    if tipos: df_filtrado = df_filtrado[df_filtrado['tipo_estabelecimento'].isin(tipos)]
    if concorrentes: df_filtrado = df_filtrado[df_filtrado['concorrente'].isin(concorrentes)]
    if status: df_filtrado = df_filtrado[df_filtrado['status'].isin(status)]

    if df_filtrado.empty:
        return {"layout": {"annotations": [{"text": "Nenhum dado para os filtros", "xref": "paper", "yref": "paper", "showarrow": False}]}}

    if tipo_mapa == 'scatter':
        fig = px.scatter_mapbox(df_filtrado, lat="latitude", lon="longitude", color="concorrente", size_max=15, zoom=4.5, center={"lat": -14.2350, "lon": -51.9253}, 
                                mapbox_style="carto-darkmatter", # ESTILIZAÇÃO
                                hover_name="municipio", custom_data=['municipio'])
    else:
        df_agregado = df_filtrado.groupby('uf').size().reset_index(name='contagem')
        fig = px.choropleth_mapbox(df_agregado, geojson=geojson_url, locations='uf', featureidkey="properties.sigla", color='contagem', 
                                   color_continuous_scale="YlOrRd", # ESTILIZAÇÃO
                                   mapbox_style="carto-darkmatter", 
                                   zoom=3.5, center={"lat": -14.2350, "lon": -51.9253}, opacity=0.7)
        fig.update_layout(coloraxis_colorbar_title_text='Nº de Clientes')
    
    fig.update_layout(margin={"r":0,"t":40,"l":0,"b":0}, paper_bgcolor=colors['plot_background'], font_color=colors['text'])
    return fig

@app.callback(
    Output('url', 'pathname'),
    Input('mapa-clientes', 'clickData'),
    State('seletor-mapa', 'value'),
    prevent_initial_call=True
)
def navigate_on_click(clickData, tipo_mapa):
    if not clickData:
        return dash.no_update

    if tipo_mapa == 'choropleth':
        estado_clicado = clickData['points'][0]['location']
        return f'/detalhes-estado/{estado_clicado}'
    
    if tipo_mapa == 'scatter':
        nome_mun_clicado = clickData['points'][0]['customdata'][0]
        return f'/detalhes-cidade/{nome_mun_clicado}'
        
    return dash.no_update

if __name__ == '__main__':
    app.run(debug=True)