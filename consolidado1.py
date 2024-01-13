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

import cufflinks as cf
import plotly.express as px
import plotly.io as pio 

# Configuração do Streamlit
st.set_page_config(page_title="Brunossf teste carteira 2024", page_icon="tada", layout="wide")
st.title('Trend following (6 meses)') #título da página

def list_useful_dates(reference_date):
    useful_dates = []
    useful_dates.append(reference_date - timedelta(days=1)) #1 dia antes
    for i in range(1, 6): #6 = 5 datas +1, exclusive
        # Calcula a nova data baseada na data de referência e no espaçamento de 30 dias
        new_date = reference_date - timedelta(days=i * 30)        
        useful_dates.append(new_date)
    return useful_dates

reference_date = st.date_input("Digite a data de referência:")

if reference_date:    
    result = list_useful_dates(reference_date)    

# Widget de botão
execute_button = st.button("Executar")

if reference_date and execute_button:
    ############testar essas datas    
    lista_data = pd.DataFrame(columns=['Adj Close'])
    
    with st.expander("cálculo das datas"):
        "calculando as datas úteis..."
        for entry in result:
            z = entry
            zz = z + timedelta(days=1)        
        
            while True:
                data1 = pd.DataFrame(yf.download('VALE3.SA', start=z, end=zz, progress=False)['Adj Close'])
                
                if data1.shape[0] > 0:
                    lista_data = pd.concat([lista_data, data1])
                    break  # Saia do loop interno se os dados foram baixados com sucesso
                    
                st.write(f'{data1.shape[1]} datas válidas')
                new_date_z = z - timedelta(days=1)
                new_date_zz = new_date_z + timedelta(days=1)
                st.write("Data inválida. Obtendo novos valores...")
                
                # if new_date_z < limite_inferior:  # Defina a condição de saída adequada
                #     break  # Saia do loop interno se atingir uma condição de parada
                    
                z = new_date_z
                zz = new_date_zz
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
    #retirar as que tem 11 no nome
    # filter the rows that contain the substring
    substring = '11'
    filter = df2['stock'].str.contains(substring)
    filtered_df = df2[~filter]
    df2 = filtered_df
    "Obtidos os valores, excluindo ativos com '11'"    
    
    @st.cache_data
    def lista():
        sfx = '.SA'
        acoess = df2['stock'].apply(lambda x: f"{x}{sfx}").values.tolist()
        return acoess
    
    acoess = lista() #ajustados os nomes dos ativos para uso no yfinance
        
    inicio = lista_data.index[-1] #ultimo da lista
    fim = lista_data.index[0] #primeiro da lista
    
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
    ultima_linha = data_yf.iloc[-1]
    novo_pd = pd.DataFrame(data_yf.iloc[-1,:]) #pra poder transpor
    novo_pd = novo_pd.transpose()        
    dfxx2 = pd.concat([dfxx, novo_pd])
    "dataframe filtrado!"
    ##filtrando o data_yf
    
    ##segundo bloco
    "ajustando o dataframe..."
    teste2 = dfxx2.copy()
    teste2.index = pd.to_datetime(teste2.index).strftime('%d-%m-%Y')
    teste2 = teste2.round(decimals = 2)
    df_pivot = teste2.T #para transpor
    
    #Jogando o nome das ações para uma coluna (só depois de transpor)
    df_pivot = df_pivot.reset_index() #ao resetar o index, o nome das ações fica em uma coluna 'index'.
    df_pivot = df_pivot.rename(columns={'index': 'ação'}) #renomeia essa coluna para 'ação'
    #df_pivot deve ter a coluna 'ação' e exatamente 6 colunas de datas    
    #excluir as colunas excedentes, se houver
    if df_pivot.shape[0] == 7:
        df_pivot = df_pivot.drop(df_pivot.columns[1], axis=1)
    "dataframe ajustado!"
    ##segundo bloco
    
    ##calculando 'ponderado'
    "calculando o fator de ponderação..."
    def calcular_resultado(row):    
        varx5 = (row[1] / row[6]) - 1 #lembrando que o mês 5 está na coluna 1
        varx4 = (row[2] / row[6]) - 1 #lembrando que o mês 4 está na coluna 2
        varx3 = (row[3] / row[6]) - 1 #lembrando que o mês 3 está na coluna 3
        varx2 = (row[4] / row[6]) - 1 #lembrando que o mês 2 está na coluna 4
        varx1 = (row[5] / row[6]) - 1 #lembrando que o mês 1 está na coluna 5
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
    
    ##2 colunas, para a tabela e para o MACD
    col1, col2 = st.columns(2)
    with col1:
        ##filtrando  FR > 90
        "obtendo somente ações com FR > 90..."
        new_df = df_pivot[['ação','FR']]
        new_df = new_df.query('FR >= 90')
        new_df.reset_index(inplace=True, drop=True) #drop joga fora a coluna com o index anterior    
        # Adicionando uma nova coluna com o preço mais recente para cada ação em new_df
        new_df['preço mais recente'] = new_df['ação'].apply(lambda x: dfxx2[x][-1])
        st.dataframe(new_df.round(decimals = 3), hide_index=True)
        ##filtrando  FR > 90
    
    with col2:
        st.write("data de hoje:", reference_date) #FALTA CONFIGURAR ESSA DATA
        
        ##análise do MACD das ações selecionadas
        # Lista de símbolos de ações
        lista = new_df['ação'].tolist()    
        new_df = new_df.set_index('ação') #depois de gerar a lista
        new_df = new_df.round(decimals = 3)
        
        # Loop pelas ações na lista
        @st.cache_data
        def calcula_macd():
            for simbolo in enumerate(lista):
                # Obtém os dados do Yahoo Finance            
                dadosx = yf.download(simbolo[1], start=inicio, end=fim, progress=False)
                p = new_df.loc[simbolo[1], 'preço mais recente']                
                
                macd = ta.trend.macd(dadosx['Adj Close']) # Calcula o MACD        
                # Verifica se o MACD está positivo e ascendente
                if macd[-1] > 0 and macd[-1] > macd[-2]:            
                    st.write(f'{simbolo[1]}: MACD positivo ascendente, R${p}') #pra mostrar o preço também
        
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
    dadosx = yf.download(choice, start=inicio, end=fim, progress=False)
    dadosx.sort_index(ascending=True, inplace=True) #organiza pelo index, do mais antigo pro mais novo, pra fazer o gráfico na ordem certa   
    "ok!"
    ##porque tem que ser o df só da ação selecionada pra gerar o gráfico

    ##configuração do cufflinks    
    cf.go_offline()
    cf.set_config_file(world_readable=True, theme='white') 
    #pio.renderers.default = "notebook" # should change by looking into pio.renderers
    ##configuração do cufflinks    

    ## grafico com o cufflinks
    qf = cf.QuantFig(dadosx, kind='candlestick', name=choice, title=choice)
    qf.add_bollinger_bands()
    qf.add_sma(name='sma20', color='red')
    qf.add_volume()    
    fig = qf.iplot(asFigure=True, dimensions=(800, 400), up_color='green', down_color='red')
    ## grafico com o cufflinks

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