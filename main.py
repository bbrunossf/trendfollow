#!/usr/bin/env python
# coding: utf-8

# # Install
# 

# In[1]:


#!pip install -q yfinance==0.2.40 (tive que atualizar para a 0.2.54, porque a anterior estava dando erro de 'too many requests'
#!pip install -q ta
#!pip install TA-Lib


# In[2]:


#!pip install -q dash dash_bootstrap_components


# In[3]:


#!pip install -q mplfinance #só faz gráfico estático, nao gostei


# # import

# In[4]:


#bases
import pandas as pd
import numpy as np
import math
from datetime import datetime, timedelta
import requests


# In[5]:


#dash
import dash
from dash import dcc, html, Input, Output, State, dcc
import dash_bootstrap_components as dbc
from dash import dash_table


# In[6]:


#graficos
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
#import mplfinance as mpf


# In[7]:


#financas
import yfinance as yf
import talib as ta


# In[8]:


#controle de erros do yfinance (suprimir mensagens)
import logging
logging.getLogger('yfinance').setLevel(logging.CRITICAL)


# # Funções

# In[9]:


#função para gerar um dataframe com as colunas de acordo com o conteúdo
def gera_df(df):
    return dash_table.DataTable(        
            id='table',            
            columns=[{"name": i, "id": i} for i in df.columns],
            data=df.to_dict('records'))


# In[10]:


#função para calcular o FR
def calcular_resultado(row):
    varx5 = (row.iloc[1] / row.iloc[6]) - 1 #lembrando que o mês 5 está na coluna 1
    varx4 = (row.iloc[2] / row.iloc[6]) - 1 #lembrando que o mês 4 está na coluna 2
    varx3 = (row.iloc[3] / row.iloc[6]) - 1 #lembrando que o mês 3 está na coluna 3
    varx2 = (row.iloc[4] / row.iloc[6]) - 1 #lembrando que o mês 2 está na coluna 4
    varx1 = (row.iloc[5] / row.iloc[6]) - 1 #lembrando que o mês 1 está na coluna 5
    return (varx5*math.sqrt(5) + varx4*math.sqrt(4) + varx3*math.sqrt(3) + varx2*math.sqrt(2) + varx1*math.sqrt(1) ) / 8.382


# In[11]:


#Revisão da função para calcular o FR (sugestão do ChatGPT)
# import math

# def calcular_resultado(row):
#     total = 0
#     for i in range(1, 6):
#         variacao = (row.iloc[i] / row.iloc[6]) - 1
#         total += variacao * math.sqrt(6 - i)
#     return total / 8.382
#nota: 8.382 é a soma das raizes de 1 a 5


# In[12]:


#função para baixar o preço de fechamento das ações filtradas, em todos os dias do intervalo
#só preciso de todos os dados das ações com FR > 90
def baixa(acoess, lista_data, inicio, fim):
    print("baixando dados...")
    data_yf = yf.download(acoess, start=inicio, end=fim, progress=True)['Close'] #só a coluna que interessa, não tem mais a coluna 'Adj Close'?
    #print(data_yf)
    if data_yf.size > 0:
        print("ok, o df não está vazio aqui")
    data_yf = calcular_media_movel(data_yf)
    
    if data_yf.size > 0:
        print("ok, está calculando as médias")
    #print(data_yf)
    
    # Converter lista_data de datetime.date para datetime64[ns]
    lista_data_datetime = pd.to_datetime([pd.Timestamp(d) for d in lista_data])
    df = data_yf.loc[data_yf.index.isin(lista_data_datetime)]
    #print(f"df filtrado com as datas úteis de 6 meses: {df})")
    #df = data_yf.loc[data_yf.index.isin(lista_data)] #lista_data agora é lista de datetime
    
    df.index = pd.to_datetime(df.index).strftime('%d-%m-%Y')
    df = df.round(decimals = 2)
    dff = df.T #para transpor
    print(f"df após transpor: {dff.head}")
    dff.dropna(axis=0, inplace=True) #nao posso mais tirar os vazios porque tem vazios na media movel    
    
    df_pivot = dff.reset_index() #ao resetar o index, o nome das ações fica em uma coluna 'index'.    
    df_pivot = df_pivot.rename(columns={'Ticker': 'ação'}) #renomeia essa coluna para 'ação'       

    #retirar as colunas se passar de 7 (precisa mesmo?)
    if df_pivot.shape[1] > 7:
        df_pivot = df_pivot.drop(df_pivot.columns[1], axis=1)

    #calcula o ponderado (senão ia ter que rodar a função duas vezes?)
    df_pivot['Ponderado'] = df_pivot.apply(lambda row: calcular_resultado(row), axis=1)
    
    return df_pivot


# In[13]:


#função para ordernar o DF (filtrar, só no callback)
def ordena_df(df):
    df_ordenado = df.sort_values(by='Ponderado', ignore_index=False)
    df_ordenado['C'] = np.arange(df_ordenado.shape[0])
    df_ordenado['FR'] = ( ( df_ordenado.shape[0] - df_ordenado['C']   ) /df_ordenado.shape[0] ) * 100
    df_ordenado = df_ordenado.sort_values(by='FR', ascending=False, ignore_index=False)
    return df_ordenado


# In[14]:


#calcular o ATR
def calculate_stop_atr(entry_price, atr, atr_multiplier=3):
    stop_loss = entry_price - (atr * atr_multiplier)
    return stop_loss


# In[15]:


#listar as 6 datas iniciais de referência 
def list_useful_dates(reference_date):  
    reference_date = datetime.strptime(reference_date, '%Y-%m-%d').date()
    useful_dates = []
    useful_dates.append(reference_date - timedelta(days=1)) #1 dia antes
    for i in range(1, 6): #6 = 5 datas +1, exclusive
        # Calcula a nova data baseada na data de referência e no espaçamento de 30 dias
        new_date = reference_date - timedelta(days=i * 30)
        useful_dates.append(new_date)
    print(f"resultado das datas iniciais: {useful_dates}")
    return useful_dates


# In[16]:


#testar as datas tentando baixar dados da VALE (só para validar as datas)
def temp1(result):
    lista_data=[]
    for date in result:
        success = False
        current_date = date
        while not success:
            try:            
                current_date_str = current_date.strftime('%Y-%m-%d')
                end_date_str = current_date + timedelta(days=1)
                end_date_str = end_date_str.strftime('%Y-%m-%d')
                data = yf.download('VALE3.SA', start=current_date_str, end=end_date_str)            
                # Verifica se o dataframe não está vazio
                if not data.empty:
                    data_n = data.index.date[0] #só preciso da data, não preciso do preço
                    lista_data.append(data_n)
                    success = True
                    #print("uma data valida" , data_n)            
                else:
                    # Se o dataframe estiver vazio, tenta o dia anterior
                    print('data inválida. Testando dia anterior...')
                    current_date = current_date - timedelta(days=1)                
            except Exception as e:
                    print("Erro", e)
    return lista_data


# In[17]:


#função para baixar os nomes de todos os ativos, e filtrar pelo volume e 
#preço mínimo desejados
def dados_brapi():
    volume_min = 200_000
    preco_min = 3

    r = requests.post('https://brapi.dev/api/quote/list?sortBy=name')
    res = r.json() #transforma em dados legiveis
    #global df #pra poder usar fora da função
    df = pd.DataFrame.from_dict(res['stocks']) #cria dataframe a partir da key do dict da lista 'res'
    dff = df[ (df['volume'] > volume_min) &  (df['close'] > preco_min) ]

    dff = dff[['stock', 'name', 'close', 'sector', 'volume']].sort_values(by='stock')
    substring = ['11', '32']
    dff_negative = dff['stock'].str.contains('|'.join(substring))
    dff = dff[~dff_negative]

    #incluir o sufixo .SA
    sfx = '.SA'
    acoess = dff['stock'].apply(lambda x: f"{x}{sfx}").values.tolist() 
    
    #return dff   
    return acoess #só preciso dos nomes das ações filtradas pelo preço e volume


# In[18]:


#função para pegar outros dados usando yfinance
def get_stock_data_yfinance(ticker):
    stock = yf.Ticker(ticker)
    stock_info = stock.info
    
    stock_data = {
        "name": stock_info.get("longName"),
        "sector": stock_info.get("sector"),
        "52_week_high": stock_info.get("fiftyTwoWeekHigh")
    }
    return stock_data


# In[19]:


def calcular_media_movel(df, window=20):
    """
    Adiciona uma coluna com a média móvel de 20 dias ao DataFrame.
    
    Parâmetros:
    df (DataFrame): DataFrame com os preços das ações.
    window (int): Tamanho da janela para a média móvel (default 20 dias).
    
    Retorno:
    DataFrame: DataFrame com uma nova coluna 'media_movel_20'.
    """
    
    # Calcula a média móvel usando a função rolling e atribui ao DataFrame
    dff = df.rolling(window=window).mean()        
    return dff


# ## Teste de funcionamento das funções

# In[20]:


#lista = dados_brapi()


# In[21]:


#reference_date = '2025-03-10'
#lista_datas = list_useful_dates(reference_date)


# In[22]:


#lista_datas


# In[23]:


#current_date = lista_datas[0]
#print(current_date)
#current_date_str = current_date.strftime('%Y-%m-%d')


# In[24]:


#end_date_str = current_date + timedelta(days=1)
#end_date_str = end_date_str.strftime('%Y-%m-%d')
#print(end_date_str)


# In[25]:


#datas_selecionadas = temp1(lista_datas)
#datas_selecionadas


# In[26]:


#inicio = datas_selecionadas[-1] - timedelta(days=20)
#fim = datas_selecionadas[0] + timedelta(days=1)
#inicio, fim


# In[27]:


#lista = dados_brapi() #lista de ações, com prefixo SA3
#data_yf = baixa(lista, datas_selecionadas, inicio, fim)
#baixa(lista)
#data_yf
#yf.download(lista, start=inicio, end=fim, progress=True)['Close'] #só a coluna que interessa


# ## Funções financeiras

# In[28]:


def calculate_bollinger_bands(df, window=20, num_std=2):
    """
    Calcula as Bandas de Bollinger.

    Parameters:
    - df: DataFrame contendo os dados
    - column: Nome da coluna para calcular as Bandas de Bollinger
    - window: Tamanho da janela para o cálculo
    - num_std: Número de desvios padrão para as bandas superior e inferior

    Returns:
    - DataFrame com as colunas 'sma', 'upper_band' e 'lower_band' adicionadas
    """
    df['sma'] = ta.SMA(df['Close'], timeperiod=window)
    df['upper_band'], df['middle_band'], df['lower_band'] = ta.BBANDS(df['Close'], timeperiod=window, nbdevup=num_std, nbdevdn=num_std, matype=0)
    return df


# In[29]:


def add_bollinger_traces(fig, df):
    """
    Adiciona os traces das Bandas de Bollinger ao gráfico.

    Parameters:
    - fig: objeto figura plotly
    - df: DataFrame contendo as colunas 'datetime', 'sma', 'upper_band' e 'lower_band'
    """
    # Adiciona a linha SMA
    fig.add_trace(go.Scatter(x = df.index,
                             y = df['sma'],
                             line_color = 'black',
                             name = 'sma'),
                  row = 1, col = 1)

    # Upper Band
    fig.add_trace(go.Scatter(x = df.index,
                             y = df['upper_band'],
                             line_color = 'gray',
                             line = {'dash': 'dash'},
                             name = 'upper band',
                             opacity = 0.5),
                  row = 1, col = 1)

    # Lower Band fill in between with parameter 'fill': 'tonexty'
    fig.add_trace(go.Scatter(x = df.index,
                             y = df['lower_band'],
                             line_color = 'gray',
                             line = {'dash': 'dash'},
                             fill = 'tonexty',
                             name = 'lower band',
                             opacity = 0.5),
                  row = 1, col = 1)


# In[30]:


def add_macd(fig, df):    
    # Adiciona a MACD
    fig.add_trace(go.Scatter(x = df.index,
                             y = df['MACD'],
                             line_color = 'black',
                             name = 'MACD'),
                  row = 3, col = 1)

    # MACD_Signal
    fig.add_trace(go.Scatter(x = df.index,
                             y = df['MACD_Signal'],
                             line_color = 'gray',
                             line = {'dash': 'dash'},
                             name = 'MACD_Signal',
                             opacity = 0.5),
                  row = 3, col = 1)

    # MACD_Hist
    fig.add_trace(go.Scatter(x = df.index,
                             y = df['MACD_Hist'],
                             line_color = 'gray',
                             line = {'dash': 'dash'},                             
                             name = 'MACD_Hist',
                             opacity = 0.5),
                  row = 3, col = 1)


# # Componentes do Layout

# In[31]:


#titulo
titulo = html.H1('Dash Finance')


# In[32]:


hoje = datetime.today()
hoje = datetime.date(hoje)
hoje


# In[33]:


#seletor de data de referencia
reference_date = dcc.DatePickerSingle(id='data-referencia', date=hoje, display_format='DD/MM/YYYY')


# In[34]:


#linha horizontal1
linha1 = html.Hr()


# In[35]:


#vazio para checar mensagens
vazio = html.Div(id='vazio')


# In[36]:


#botao de executar
botao_executar = dbc.Button('Executar', id='botao-executar')


# In[37]:


#collapse para mostrar o avanço dos calculos
espaco = dbc.Collapse([
          dbc.Textarea(id='textarea', style={'width': '100%', 'height': '300px'}),         
        ],
        id="horizontal-collapse", is_open=True)


# In[38]:


#tabela para abrir o dataframe de saída
#aí o output tem que ser um html.Div?
df = pd.DataFrame()
tabela1 = dash_table.DataTable(
            id='table',            
            columns=[],
            data=[])
            


# In[39]:


#Div vazio pra receber o elemento dash_table
tabela2 = html.Div(id='table2')


# In[40]:


#Div vazio pra receber o elemento dash_table
tabela3 = html.Div(id='table3')


# In[41]:


#radio buttons com as ações selecionadas
#botoes_acoes = dcc.RadioItems(id='radio-buttons', options=[], value=None )


# In[42]:


#grafico comos indicadores:
#bollinger, médias moveis, volume, Stop ATR, MACD, IFR
grafico1 = dcc.Graph(
        id='graph1',
        figure={
        'data': []}
    )


# In[43]:


#grafico para mostrar os setores das ações
grafico2 = dcc.Graph(
        id='graph2',
        figure={
        'data': []}
    )


# In[44]:


#linha horizontal2
linha2 = html.Hr()


# # Layout

# In[45]:


app = dash.Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.BOOTSTRAP])


# In[46]:


app.layout = dbc.Container([
    html.Div([
        titulo,
        reference_date,
        botao_executar,
        dcc.Store(id='lista-data'),
        dcc.Store(id='dados-acoes'),
        dcc.Store(id='dados-processados'),  # Store para guardar os dados processados
        dcc.Store(id='df-grande'), #Store pra guardar o df dos 6 meses das ações FR >90
        dcc.Store(id='stock-types'), #Store pra guardar o ultimo df com o tipo das ações
        linha1,]),
    dbc.Row([
      dbc.Col([
            vazio,
            espaco,
            tabela1,
            tabela2,
            tabela3,
            ])
      ]),
    #outra linha com duas colunas pra colocar os botoes ao lado do grafico
    dbc.Row([
        #dbc.Col([botoes_acoes], width=2),
        dbc.Col([grafico1], width=12),
        ]),
    #outra linha para mostrar o grafico de setores
    dbc.Row([
        linha2,
        dbc.Col( width=2),
        dbc.Col([grafico2], width=10),
        ]),
    ])


# ## Callbacks e Run

# In[47]:


# Callback para gerar datas úteis
#gera uma lista de datas testadas e validadas
@app.callback(
    [Output('lista-data', 'data'), #store
    Output('textarea', 'value')],
              
    Input('botao-executar', 'n_clicks'),
    State('data-referencia', 'date'),    
    prevent_initial_call=True
)
def gerar_datas(n_clicks, date):
    if n_clicks:
        result = list_useful_dates(date) #texto
        #testar as datas e gerar a lista de datas atualizadas (lista_data)
        lista_data = temp1(result) #lista
        msg = "Datas calculadas...\n"
        return [lista_data, msg] #e joga no store e na area de texo
    return [None, None]


# In[48]:


# Callback para baixar dados de ações + a mensagem no textarea
#gera um dict multiindex com os dados das ações filtradas pelo preço e volume
@app.callback(
    [Output('dados-acoes', 'data'), #store
     Output('textarea', 'value', allow_duplicate=True)],
    
    Input('lista-data', 'data'),
    State('textarea', 'value'),
    prevent_initial_call=True
)
def baixar_dados_acoes(lista_data, current_msg):
    if lista_data:
        #print(f"item da lista_data é do tipo {type(lista_data[0])}")
        lista_data_datetime = pd.to_datetime([pd.Timestamp(d) for d in lista_data])
        print(f"lista de datas em formato datetime: {lista_data_datetime}")
        
        acoes = dados_brapi() #lista de ações, com prefixo SA3
        print(acoes[0:10]) #só pra ver os dados
        inicio = lista_data_datetime[-1] - timedelta(days=40)
        print(f"data de inicio:{inicio}")
        fim = lista_data_datetime[0] + timedelta(days=1)
        print(f"data de fim:{fim}")
        data_yf = baixa(acoes, lista_data, inicio, fim)
        print(type(data_yf))
        print(data_yf.head())
        msg = current_msg + "Ações filtradas e dados baixados...\n"
        return [data_yf.to_dict(), msg] #df já com o ponderado calculado;salva no store
    return[None, None]


# In[49]:


# Callback para processar os dados e armazenar no dcc.Store
#gera um records com as colunas: ação, datas (com os preços), C, FR
@app.callback(
    [Output('dados-processados', 'data'),
    Output('textarea', 'value', allow_duplicate=True)], #store
    
    Input('dados-acoes', 'data'),
    State('textarea', 'value'),
    prevent_initial_call=True
)
def processar_dados(data_yf, current_msg):
    if data_yf:
        print("data_yf recebido")
        #print(data_yf.columns)
        df = pd.DataFrame.from_dict(data_yf)
        dff = ordena_df(df)
        df_final = dff[dff['FR'] >= 80]
        msg = current_msg + "Ações selecionadas pelo FR > 90 e salvo na memória...\n"
        return [df_final.to_dict('records'), msg] #nao precisa exibir ele, só salvar na memoria
        


# In[50]:


#revisão do callback, chamando a yfinance somente uma vez
#Callback para baixar os dados das ações filtradas
#gera um df multinivel com as ações com FR > 90, no periodo inteiro
@app.callback(
    [#Output('table3', 'children'), #melhor jogar em outro dcc store
    Output('df-grande', 'data'), #store
    Output('textarea', 'value', allow_duplicate=True)],
    
    Input('dados-processados', 'data'),
    Input('lista-data', 'data'),
    State('textarea', 'value'),
    prevent_initial_call=True
    
)
def gera_indicadores(processed_data, lista_datas, current_msg):
    if processed_data and lista_datas:
        print("datas úteis recebidas e dados processados também")
        #data é um dict, precisa passar de volta para df
        df = pd.DataFrame(processed_data) #é assim ou from_dict?
        acoes_selecionadas = df['ação'].to_list()
        
        
        
                    
        #agora baixa tudo das ações selecionadas
        lista_data_datetime = pd.to_datetime([pd.Timestamp(d) for d in lista_datas])
        inicio = lista_data_datetime[-1] - timedelta(days=40)
        fim = lista_data_datetime[0] + timedelta(days=1)
        #baixa agrupando por Ticker
        df_acoes_selecionadas = yf.download(acoes_selecionadas, start=inicio, end=fim, progress=True, group_by='Ticker')
        
        # transforma o dataframe: faz o stack para criar um  multi-index (Date, Ticker), 
        #e então reseta os índices para jogar o 'Ticker' em uma coluna
        df_acoes_selecionadas = df_acoes_selecionadas.stack(level=0).rename_axis(['Date', 'Ticker']).reset_index(level=1)

        #print do df_acoes_selecionadas, pra ver se tem o Ticker
        print(f"colunas do df recebido do yfinance, após o stack e o reset_index: {df_acoes_selecionadas.columns}")
        #resposta: ['Ticker', 'Open', 'High', 'Low', 'Close', 'Volume'], dtype='object', name='Price')

        #faz um loop para criar dfs separados pra cada ação
        #faz uma lista de dfs
        dataframes = []
        for acao in acoes_selecionadas: #deixei porque a lista de acoes ainda é recebida
            #df_acao = yf.download(acao, start=inicio, end=fim, progress=False)
            df_acao = df_acoes_selecionadas[df_acoes_selecionadas['Ticker'] == acao]
            df_acao.reset_index(inplace=True)
            df_acao['Acao'] = acao  # Adicionar coluna com o nome da ação

            #inserir aqui o ATR como uma coluna            
            df_acao['ATR(14)'] = ta.ATR(
                                high=df_acao['High'],
                                low=df_acao['Low'],
                                close=df_acao['Close']
                                )
            print(df_acao.head())
            
            atr_factor = 1.5
            df_acao['Stop_ATR'] = df_acao['Close'] - (atr_factor * df_acao['ATR(14)'])
            #alterado de Adj Close para Close com a versão 0.2.54 do yfinance
            df_acao['Risco_%'] = ((df_acao['Close'] - df_acao['Stop_ATR']) / df_acao['Stop_ATR']) * 100
            
            dataframes.append(df_acao)
        
        # Concatenar todos os dataframes
        df_acoes_selecionadas = pd.concat(dataframes, ignore_index=True)
        # Converter o DataFrame para uma lista de dicionários serializáveis
        data = df_acoes_selecionadas.to_dict('records')                       
        msg = current_msg + "Dataframes das ações criados...\n"
        return [data, msg]
       


# In[52]:


#callback para fazer a tabela
#a partir do df em 'df-grande', ação por ação:
    #cria um df temporario com nome, preço ultimo, preço 52 semanas
    #concatena tudo num df só

@app.callback(
    [Output('table3', 'children'), #é um div vazio; retornar um dash table completo
    Output('textarea', 'value', allow_duplicate=True)],
    
    Input('df-grande', 'data'), #data é um records
    State('textarea', 'value'),
    prevent_initial_call=True
)
def teste(data, current_msg):
    if data is not None:
        global df
        #df = pd.DataFrame.from_dict(data)
        df = pd.DataFrame.from_records(data)
        print(df.head())
        print(f'as colunas do df-grande são {df.columns}')
        #alterado de Adj Close para Close com a versão 0.2.54 do yfinance
        acoes = df['Acao'].unique()        
        df_geral = pd.DataFrame(columns=['Close', 'Acao', 'preco_max52', 'Risco_%'])        
        for acao in acoes:
            df_acao = df[df['Acao'] == acao] #aqui ele tá filtrado mas tem todas as colunas
            #a linha com o último preço é a ultima
            df_acao = pd.DataFrame([df_acao.loc[df_acao.index[-1], ['Close', 'Acao', 'Risco_%']]])                           
            #obter o preço máximo das 52 semanas
            #max52 = yf.Ticker(acao).history(period='1y')['High'].max()
            x= yf.ticker.Ticker(acao)
            ultima = df.iloc[df.index[-1], 0]
            data_inicial = pd.to_datetime(ultima).date()
            final = pd.to_datetime(ultima).date() - timedelta(weeks=52)
            #print(f"data inicial ficou {data_inicial}")
            #print(f"data final ficou {final}")
            #max52 = x.history(start=ultima, end=final)['High'].max()
            max52 = x.history(start=final, end=data_inicial)['High'].max()
            
            df_acao['preco_max52'] = max52

            #colunas extras
            colunas = ['industry', 'sector', 'symbol', 'shortName']            
            stock = yf.Ticker(acao)
            stock_info = stock.info
            stock_data = {
                    "industry": stock_info.get("industry"),        
                    "sector": stock_info.get("sector"),                            
                    "Acao": stock_info.get("symbol"),                      
                    "shortName": stock_info.get("shortName"),   
                    }            
            dff_temp = pd.DataFrame([stock_data])
            
            #mesclar df_acao com dff_temp
            df_acao = pd.merge(df_acao, dff_temp, how='left', on='Acao')
            
            df_geral = pd.concat([df_geral, df_acao])
        
        #alterado de Adj Close para Close, com a versão 0.2.54
        df_geral['distancia'] = np.where(df_geral['preco_max52'] != 0, ((df_geral['preco_max52'] - df_geral['Close']) / df_geral['preco_max52']) * 100, None)
        df_geral['Retorno_Risco'] = df_geral['distancia'] / df_geral['Risco_%']
        df_geral = df_geral[['Acao', 'shortName', 'industry', 'sector', 'preco_max52',\
                            'Close', 'distancia', 'Risco_%', 'Retorno_Risco']]
        df_geral = df_geral.round(decimals = 2)
        msg = current_msg + "Tabela geral com preços máximos e diferenças...\n"
        df_geral.to_csv('teste.csv', index=False, decimal=',', sep=';')
        return [dash_table.DataTable(        
                    id='tabley',            
                    columns=[{"name": i, "id": i} for i in df_geral.columns],
                    data=df_geral.to_dict('records'),
                    active_cell = {'row': 0, 'column': 0},
                    #page_size= 10,    
                    page_action="native",
                    sort_action='native'),
               msg]
    return[None, None]
    


# In[53]:


# #callback para atualizar os radio buttons
# #popula com os nomes das ações com FR > 90
# @app.callback(
#     Output('radio-buttons', 'options'),
#     Input('dados-processados', 'data')
# )
# def mostra_botoes(data):
#     if data is not None:
#         df = pd.DataFrame.from_records(data)
#         return [{'label': col, 'value': col} for col in df['ação'].unique()]
#     else:
#         return []


# In[54]:


#callback para os indicadores, só de uma ação (a ação selecionada)
#filtra o df geralzão e pega só da ação selecionada
#macd e o Stop ATR
#faz o gráfico com o cufflinks adicionando outros indicadores
@app.callback(
    Output('graph1', 'figure'),
   # Output('textarea', 'value', allow_duplicate=True)],

        
    
    #Input('radio-buttons', 'value'),
    Input('tabley', 'active_cell'),
    State('tabley', 'data'),
    State('df-grande', 'data'), #contem todas as ações
    State('textarea', 'value'),
    prevent_initial_call=True #precisa dele se for usar como input algo que não está diretamente no layout
)
def cria_grafico(selecao, tabley_data, df_dict, current_msg):
    #Na revisão, não preciso checar se selecao is not None porque lá ao criar o datatable eu ja defini
    #um active_cell padrao, mas aí a tabela não pode ser multipage porque ao mudar de página não vai ter
    #celula ativa
    #if valor is not None and selecao is not None:
    num_linha = selecao['row']
    acao = str(tabley_data[num_linha]['Acao'])        
    print(f"o valor da ação pelo click é {acao}")
    
    #print(f"o valor da ação pelo radio button é {valor}")
    
    
    df_acoes_selecionadas = pd.DataFrame.from_dict(df_dict)
    #print(f"o inicio do df grande é {df_acoes_selecionadas.head()}")
    #global df_acao
    #df_acao = None

    
    #print(f"colunas do df antes de filtrar: {df_acao.columns}")
    df_acao = df_acoes_selecionadas[df_acoes_selecionadas['Acao'] == acao]
    
    #tira linhas que tenham zero em alguma coluna
    df_acao = df_acao.loc[~(df_acao == 0).any(axis=1)]
    
    #reseta o indice
    df_acao = df_acao.reset_index(drop=True)
    
    #print(f"o df da ação é {df_acao.head()}")
    
    #print(f"os valores da coluna Acao no df filtrado são {df_acao['Acao'].unique()}")
    
    #ajustar o index
    df_acao['Date'] = pd.to_datetime(df_acao['Date'])
    df_acao = df_acao.set_index('Date')
    
    # ##criar fig                      
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, row_heights=[0.6, 0.2, 0.2], vertical_spacing=0.05)

    #traco1
    trace1 = go.Candlestick(
        x=df_acao.index,
        open=df_acao['Open'],
        high=df_acao['High'],
        low=df_acao['Low'],
        close=df_acao['Close']
    )

    df_acao['ATR(14)'] = ta.ATR(
    high=df_acao['High'],
    low=df_acao['Low'],
    close=df_acao['Close']
    )
    atr_factor = 1.5
    df_acao['Stop_ATR'] = df_acao['Close'] - (atr_factor * df_acao['ATR(14)'])

    #graficos de linha são scatter do tipo line
    trace2 = go.Scatter(mode='lines', x=df_acao.index, y=df_acao['Stop_ATR'], line_shape='hv')

    

    fig.add_traces([trace1, trace2])
    df_acao = calculate_bollinger_bands(df_acao)
    add_bollinger_traces(fig, df_acao)
    

    #volume tem que ser subplot
    fig.add_trace(go.Bar(
        x = df_acao.index, y = df_acao['Volume'], showlegend=False, 
        marker_color=df_acao.apply(lambda row: 'green' if row['Close'] > row['Open'] else 'red', axis=1)),
        row=2, col=1)
    #adicionar o volume médio
    ## Calcular o volume médio
    df_acao['Volume_Mean'] = df_acao['Volume'].rolling(window=20).mean()
    
    fig.add_trace(go.Scatter(
        x=df_acao.index,
        y=df_acao['Volume_Mean'],
        mode='lines',
        line=dict(color='blue', width=2),
        name='Volume Médio'),
        row=2, col=1)

    #agora com MACD
    df_acao['MACD'], df_acao['MACD_Signal'], df_acao['MACD_Hist'] = ta.MACD(df_acao['Close'], fastperiod=12, slowperiod=26, signalperiod=9)
    add_macd(fig, df_acao)
    
    #fig.update(layout_xaxis_rangeslider_visible=False)
    # Atualizando layout e altura
    fig.update_layout(
        height=1000,  # Define a altura da figura
        xaxis_rangeslider_visible=False
    )
    fig.update_xaxes(
        rangebreaks=[
            dict(bounds=["sat", "mon"]), #hide weekends
        ])            
    # ##criar fig    
    msg = current_msg + 'Grafico criado!'
    return fig
    #return[None, msg]
    #return None 


# In[55]:


#callback para o grafico2
@app.callback(
    Output('graph2', 'figure'),
    Input('tabley', 'data'), #a datatable resumida que é retornada dentro de table3
    prevent_initial_call=True
)
def grafico2(rows):
    if not rows:
        return dash.no_update
    df = pd.DataFrame(rows) #dados
    print(f'as colunas do df para o graph2 são {df.columns}')
    fig = px.scatter(
        df,
        x='distancia',
        y='Risco_%',
        #size='Adj Close',  
        #size='Retorno_Risco', #se for negativo da erro
        #size_max=15, #ficou pequeno independente do tamanho que coloquei
        color='sector',
        #hover_data=['Acao'],
        text='Acao',
        hover_data=['Retorno_Risco'],
        labels={},
        title='Grafico de bolhas, por setor'
    )

    #adicionando as linhas que irão dividir os quadrantes:
    #linha vertical no meio do intervalo do eixo X (distancia)    
    # Ponto médio para a linha vertical
    mid_x = df['distancia'].max() / 2
    mid_y = df['Risco_%'].max() / 2
    
    # Desenhando a linha vertical
    fig.add_trace(go.Scatter(
        x=[mid_x, mid_x],
        y=[df['Risco_%'].min() - 1, df['Risco_%'].max() + 1],
        mode='lines',
        line=dict(color='red', dash='dash'),
        showlegend=False
        ))
        
    #linha horizontal
    # Ponto médio para a linha horizontal    
    #mid_yy = df['Risco_%'].median()
    
    # Desenhando a linha horizontal
    fig.add_trace(go.Scatter(
        x=[df['distancia'].min() - 1, df['distancia'].max() + 1],
        y=[mid_y, mid_y],
        mode='lines',
        line=dict(color='red', dash='dash'),
        showlegend=False
        ))

    fig.update_traces(textposition="bottom right")
    
    #fig.update se precisar
    return fig
    


# In[56]:


#app.run(debug=True, port='8503', jupyter_mode="jupyterlab") #somente para ambiente local
server = app.server
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)


