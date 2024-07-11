# -*- coding: utf-8 -*-
"""
Created on Thu Jan 11 20:28:43 2024

@author: BRUNO
"""
#conteudo completo do 7datas.py

import streamlit as st
import yfinance as yf
from datetime import datetime, timedelta
import requests
import pandas as pd
import numpy as np
import math

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import ta
from ta.momentum import StochasticOscillator
from ta.volatility import AverageTrueRange

import cufflinks as cf
import plotly.express as px
import plotly.io as pio 



# Configuração do Streamlit
st.set_page_config(page_title="Brunossf teste carteira 2024", page_icon="tada", layout="wide")
st.title('Trend following (6 meses)') #título da página

st.__version__
yf.__version__
pd.__version__

"""
arrumei a função de baixar os dados
Agora tentando incluir o Stop ATR.
Já deu pra calcular uma por uma na última data, mas eu queria plotar a série no gráfico.
Tentando..
"""

def calculate_stop_atr(entry_price, atr, atr_multiplier=3):
    stop_loss = entry_price - (atr * atr_multiplier)
    return stop_loss
    
def list_useful_dates(reference_date):
    useful_dates = []
    useful_dates.append(reference_date - timedelta(days=1)) #1 dia antes
    for i in range(1, 6): #6 = 5 datas +1, exclusive
        # Calcula a nova data baseada na data de referência e no espaçamento de 30 dias
        new_date = reference_date - timedelta(days=i * 30)        
        useful_dates.append(new_date)
    return useful_dates

reference_date = st.date_input("Digite a data de referência:")

#check
# from datetime import date
# reference_date = datetime(2024, 7, 9)
#yfinance suporta string com 'YYYY-MM-DD' ou tipo datetime


if reference_date:    
    result = list_useful_dates(reference_date)    

# Widget de botão
execute_button = st.button("Executar")

# if reference_date and execute_button:
if reference_date and execute_button:
    ############testar essas datas    
    # DataFrame vazio para concatenar os dados        
    lista_data = pd.DataFrame(columns=['Adj Close'])
    
    st.write(f"result tem {len(result)} datas")
    
    # Loop para baixar os dados
    for date in result:
        success = False
        current_date = date
        while not success:
            # Formata a data atual para o formato de string
            current_date_str = current_date.strftime('%Y-%m-%d')
            end_date_str = current_date + timedelta(days=1)
            end_date_str = end_date_str.strftime('%Y-%m-%d')
            try:
                print(f"testando intervalo {current_date_str} e {end_date_str}...")
                # Baixa os dados da ação na data especificada
                data = pd.DataFrame(yf.download('VALE3.SA', start=current_date_str, end=end_date_str)['Adj Close'])
                # Verifica se o dataframe não está vazio
                if not data.empty:
                    lista_data = pd.concat([lista_data, data])
                    success = True
                else:
                    # Se o dataframe estiver vazio, tenta o dia anterior
                    current_date -= timedelta(days=1)
                    print('data inválida. Testando dia anterior...')
            except Exception as e:
                # Em caso de erro, tenta o dia anterior
                current_date -= timedelta(days=1)
                print('erro. Testando o dia anterior......')
    
    #nova lista de datas. Pegar do df completo
    # lista_data = list(lista_data.index)
    "datas ok!"
    # Continue com o restante do código aqui, se necessário
    # st.write('novas datas:')
    # st.write(lista_data)    
    ############testar essas datas    
    
    ############cópia da versão anterior
    volume_min = 200_000
    preco_min = 3
    
    @st.cache_data
    def dados_brapi():
        r = requests.post('https://brapi.dev/api/quote/list?sortBy=name')
        res = r.json() #transforma em dados legiveis
        global df #pra poder usar fora da função
        df = pd.DataFrame.from_dict(res['stocks']) #cria dataframe a partir da key do dict da lista 'res'
        df = df[ (df['volume'] > volume_min) &  (df['close'] > preco_min) ]
        return df    
    
    st.write(f"baixando dados de todos os ativos (volume mínimo de R\${volume_min:,.2f}, preço mínimo de R\${preco_min:.2f})")
    df2 = dados_brapi()
    df2 = df2[['stock', 'name', 'close', 'sector', 'volume']].sort_values(by='stock')
    #retirar as que tem 11 e 32 no nome
    # filter the rows that contain the substring
    substring = ['11', '32']
    #filter = df2['stock'].str.contains(substring)
    filter = df2['stock'].str.contains('|'.join(substring))

    filtered_df = df2[~filter]
    df2 = filtered_df
    "Obtidos os valores, excluindo ativos com '11' e com '32'"   
    
    @st.cache_data
    def lista():
        sfx = '.SA'
        acoess = df2['stock'].apply(lambda x: f"{x}{sfx}").values.tolist()
        return acoess
    
    acoess = lista() #ajustados os nomes dos ativos para uso no yfinance
        
    inicio = lista_data.index[-1] #ultimo da lista
    fim = lista_data.index[0] + timedelta(days=1) #1 dia a mais do primeiro da lista, exclusive
    
    # @st.cache_data
    def baixa():
        data_yf = yf.download(acoess, start=inicio, end=fim, progress=False)['Adj Close'] #só a coluna que interessa
        return data_yf
    
    data_yf = baixa()
    data_yf.dropna(axis=1, inplace=True) #retira os vazios
    ############cópia da versão anterior
    
    ##filtrando o data_yf
    "filtrando para as datas selecionadas..."
    dfxx = data_yf.loc[data_yf.index.isin(lista_data.index)]    
    # Pegar a última linha do DataFrame de origem e copiar para o DataFrame de destino
    # ultima_linha = data_yf.iloc[-1]
    # novo_pd = pd.DataFrame(data_yf.iloc[-1,:]) #pra poder transpor
    # novo_pd = novo_pd.transpose()        
    # dfxx2 = pd.concat([dfxx, novo_pd])
    "dataframe filtrado!"
    st.write('dataframe após filtrar')
    st.dataframe(dfxx)
    ##filtrando o data_yf
    
    ##segundo bloco
    "ajustando o dataframe..."
    teste2 = dfxx.copy()
    teste2.index = pd.to_datetime(teste2.index).strftime('%d-%m-%Y')
    teste2 = teste2.round(decimals = 2)
    df_pivot = teste2.T #para transpor
    
    
    
    #Jogando o nome das ações para uma coluna (só depois de transpor)
    df_pivot = df_pivot.reset_index() #ao resetar o index, o nome das ações fica em uma coluna 'index'.    
    df_pivot = df_pivot.rename(columns={'Ticker': 'ação'}) #renomeia essa coluna para 'ação'
    st.write('dataframe após mudar o nome da coluna')
    st.dataframe(df_pivot)
    #df_pivot deve ter a coluna 'ação' e exatamente 6 colunas de datas    
    #excluir as colunas excedentes, se houver
    if df_pivot.shape[1] > 7:
        df_pivot = df_pivot.drop(df_pivot.columns[1], axis=1)
    "dataframe ajustado!"
    ##segundo bloco
    
    ##calculando 'ponderado'
    "calculando o fator de ponderação..."
    def calcular_resultado(row):    
        varx5 = (row.iloc[1] / row.iloc[6]) - 1 #lembrando que o mês 5 está na coluna 1
        varx4 = (row.iloc[2] / row.iloc[6]) - 1 #lembrando que o mês 4 está na coluna 2
        varx3 = (row.iloc[3] / row.iloc[6]) - 1 #lembrando que o mês 3 está na coluna 3
        varx2 = (row.iloc[4] / row.iloc[6]) - 1 #lembrando que o mês 2 está na coluna 4
        varx1 = (row.iloc[5] / row.iloc[6]) - 1 #lembrando que o mês 1 está na coluna 5
        return (varx5*math.sqrt(5) + varx4*math.sqrt(4) + varx3*math.sqrt(3) + varx2*math.sqrt(2) + varx1*math.sqrt(1) ) / 8.382
    
    df_pivot['Ponderado'] = df_pivot.apply(lambda row: calcular_resultado(row), axis=1)
    "ponderação calculada!"
    ##calculando 'ponderado'
    
    ##calculo do FR
    "calculando o FR..."
    df_pivot = df_pivot.sort_values(by='Ponderado', ignore_index=False) #tem que colocar em ordem crescente de ponderado primeiro
    df_pivot['C'] = np.arange(df_pivot.shape[0]) #cria uma coluna com o numero da linha
    df_pivot['FR'] = ( ( df_pivot.shape[0] - df_pivot['C']   ) /df_pivot.shape[0] ) * 100 #total de linhas - num da linha / total de linhas
    df_pivot = df_pivot.sort_values(by='FR', ascending=False, ignore_index=False) #classifica por FR em ordem decrescente, sem descartar o índice
    
    df_final = df_pivot[(df_pivot['FR'] >= 90)]
    "FR calculado!"
    ##calculo do FR
    
    st.dataframe(df_pivot)
    
    ##2 colunas, para a tabela e para o MACD
    col1, col2 = st.columns(2)
    with col1:
        ##filtrando  FR > 90
        "obtendo somente ações com FR > 90..."
        new_df = df_pivot[['ação','FR']]
        new_df = new_df.query('FR >= 90')
        new_df.reset_index(inplace=True, drop=True) #drop joga fora a coluna com o index anterior    
        # Adicionando uma nova coluna com o preço mais recente para cada ação em new_df
        new_df['preço mais recente'] = new_df['ação'].apply(lambda x: dfxx[x].iloc[-1])
        st.dataframe(new_df.round(decimals = 3), hide_index=True)
        ##filtrando  FR > 90
    
    with col2:
        st.write("data de hoje:", reference_date.strftime("%d-%m-%Y"))
        
        ##análise do MACD das ações selecionadas
        # Lista de símbolos de ações
        lista = new_df['ação'].tolist()    
        new_df2 = new_df.set_index('ação') #depois de gerar a lista
        new_df2 = new_df2.round(decimals = 3)
        
        #filtrar o data_yf só com as ações da lista
        todos_dados = data_yf[lista]
        
        # Loop pelas ações na lista
        @st.cache_data
        def calcula_macd():            
            for simbolo, dadosx in todos_dados.items():
                p = dadosx.iloc[-1]  # ultimo preço
                macd = ta.trend.macd(dadosx)
                # verifica se macd está ascendente ou descendente
                if macd.iloc[-1] > 0 and macd.iloc[-1] > macd.iloc[-2]:         
                    st.write(f'{simbolo}: MACD positivo ascendente, R${p}') #pra mostrar o preço também
        
        st.write(calcula_macd()) #só pra escrever se tá ascendente
        ##análise do MACD das ações selecionadas
    ##2 colunas, para a tabela e para o MACD    
        
    ## salvar o que precisar para gerar os graficos
    #lista, inicio, fim
    #"salvando os dados no session_state..."
    st.session_state.lista = lista    
    st.session_state.inicio = inicio    
    st.session_state.fim = fim    
    "session_state salvo!"
    ## salvar o que precisar para gerar os graficos

##carregar o que foi salvo
if 'inicio' in st.session_state:
    inicio = st.session_state.inicio
    #"recarregando os dados..."
    
if 'fim' in st.session_state:
    fim = st.session_state.fim
    
if 'lista' in st.session_state:
    lista = st.session_state.lista
##carregar o que foi salvo
    #e aqui eu já emendo a criação do gráfico
    choice = st.selectbox("escolha a ação", lista)        
    
    ##porque tem que ser o df só da ação selecionada pra gerar o gráfico
    "baixando dados da ação selecionada..."    
    #######dadosx = yf.download(choice, start=inicio, end=fim, progress=False)
    #######dadosx.sort_index(ascending=True, inplace=True) #organiza pelo index, do mais antigo pro mais novo, pra fazer o gráfico na ordem certa   
    "ok!"
    ##porque tem que ser o df só da ação selecionada pra gerar o gráfico

    ##configuração do cufflinks    
    cf.go_offline()
    cf.set_config_file(world_readable=True, theme='white') 
    #pio.renderers.default = "notebook" # should change by looking into pio.renderers
    ##configuração do cufflinks

    #função para baixar os dados da lista
    @st.cache_data
    def baixa_lista():    
        bleh = yf.download(lista, start=inicio, end=fim, progress=True)        
        return bleh
    bleh = baixa_lista()
    dadosx = bleh.loc[:, (['Open', 'High', 'Low', 'Close', 'Volume'], choice)]
    dadosx.columns = dadosx.columns.droplevel(1)
    
    # #esse deu certo, mas uma ação de cada vez e somente o último preço
    # for i in lista:
        # df_acao = bleh.loc[:, (['Open', 'High', 'Low', 'Close', 'Volume'], i)]
        # df_acao.columns = df_acao.columns.droplevel(1)
        # st.write(f"Dados da ação {i}")
        
        # atr_indicator = AverageTrueRange(high=df_acao['High'], low=df_acao['Low'], close=df_acao['Close'], window=14)
        # df_acao['ATR'] = atr_indicator.average_true_range() #esse é um multiplicador para o preço atual
        
        # #st.dataframe(df_acao)
        
        # # Define o preço de entrada e o multiplicador ATR
        # entry_price = df_acao.iloc[-1, 3]  # última linha, coluna 3 ('Close')
        # atr_value = df_acao['ATR'].iloc[-1]  # Obtém o valor ATR mais recente
        # atr_multiplier = 3  # Multiplicador ATR
        
        # # Calcula o stop ATR
        # stop_loss = calculate_stop_atr(entry_price, atr_value, atr_multiplier)
        # stop_loss_pct = entry_price / stop_loss - 1
        # # st.write(f"Preço de Entrada: {entry_price}")
        # # st.write(f"Valor do ATR: {atr_value:.2f}")
        # # st.write(f"Stop Loss ATR: {stop_loss:.2f}")
        # st.write(f"% de perda admitido: {stop_loss_pct:.2%}")
        
    # Loop para processar cada ação na lista e plotar os gráficos com os dados e Stop ATR
    #código do chatGPT
    #não está ruim, mas plota todos os graficos, e a serie Stop ATR está vazia
    for acao in lista:
        df_acao = bleh.loc[:, (['Open', 'High', 'Low', 'Close', 'Volume'], acao)]
        df_acao.columns = df_acao.columns.droplevel(1)

        # Calcula o ATR para a ação atual
        atr_indicator = AverageTrueRange(high=df_acao['High'], low=df_acao['Low'], close=df_acao['Close'], window=14, fillna=True)
        df_acao['ATR'] = atr_indicator.average_true_range()
        
        
        # Últimos preços de fechamento e ATR
        entry_price = df_acao['Close'].iloc[-1]
        atr_value = df_acao['ATR'].iloc[-1]
        atr_multiplier = 3  # Ajustável conforme necessário

        # Calcula o Stop ATR para cada ponto de dados (considerando valores NaN)
        df_acao['Stop ATR'] = df_acao.apply(lambda row: row['Close'] - row['ATR'] * atr_multiplier, axis=1)



        # Calcula o Stop ATR
        stop_atr = calculate_stop_atr(entry_price, atr_value, atr_multiplier)
        st.write(f"Stop Loss ATR: {stop_atr:.2f}")        
        st.write(f"check: {len(df_acao)}") 
        
       
        # Plotagem do gráfico
        qf = cf.QuantFig(df_acao, title=acao, legend='top', name='Candlestick')
        qf.add_bollinger_bands()
        qf.add_sma(name='sma20', color='red')
        #qf.add_line(x=df_acao.index, y=[stop_atr]*len(df_acao), name='Stop ATR', color='blue', width=1.5)
        qf.add_volume()
        fig = qf.iplot(asFigure=True, dimensions=(1000, 400), up_color='green', down_color='red')
        
        # Adiciona linha de Stop ATR
        fig.add_trace(go.Scatter(x=df_acao.index, y=[stop_atr]*len(df_acao), mode='lines', name='Stop ATR', line=dict(color='green', width=3), connectgaps=False))
        
        
        # ## grafico com o cufflinks
        # qf = cf.QuantFig(dadosx, kind='candlestick', name=choice, title=choice)
        # qf.add_bollinger_bands()
        # qf.add_sma(name='sma20', color='red')
        # qf.add_volume()    
        # fig = qf.iplot(asFigure=True, dimensions=(800, 400), up_color='green', down_color='red')
        # ## grafico com o cufflinks

        ##ajuste final do grafico
        #update_xaxes ou update_yaxes é do plotly, que gera a fig
        fig.update_xaxes(
            rangebreaks=[
                dict(bounds=["sat", "mon"]), #hide weekends
            ]
        )    
        st.plotly_chart(fig)
        ##ajuste final do grafico
else:
    st.warning("selecione a data e clique em Executar")    

