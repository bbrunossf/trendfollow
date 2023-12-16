# -*- coding: utf-8 -*-
"""
Created on Tue Mar 14 18:34:02 2023

@author: BRUNO
"""


import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
import math
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dateutil.relativedelta import relativedelta
import ta
from ta.momentum import StochasticOscillator

import cufflinks as cf
import plotly.express as px
import plotly.io as pio 


st.set_page_config(page_title="Brunossf teste carteira 2023", page_icon=":tada:")
st.title('Trend following (6 meses)') #título da página

st.warning("INSTRUÇÕES DE USO", icon="⚠️")
st.write("A data final deve ser 2 dias menos que a data atual.  \n")
st.markdown("O aplicativo usa um intervalo de 6 meses de dados, e a variação\
        percentual entre os meses anteriores e a data final selecionada.  \n\
        As melhores ações serão aquelas que tem maior variação negativa\
        em relação à data de hoje, ou seja, nos meses anteriores o preço\
        era menor do que hoje, ponderada pelo tempo (preço mais antigo\
        tem mais peso na conta do que os preços mais novos).  \n\
        ")
#dois espaços e o \n pra ele entender que é uma quebra de linha
volume_min = 200000
preco_min = 3

@st.cache_data
def dados_brapi():
    r = requests.post('https://brapi.dev/api/quote/list?sortBy=name')
    res = r.json() #transforma em dados legiveis
    global df #pra poder usar fora da função
    df = pd.DataFrame.from_dict(res['stocks']) #cria dataframe a partir da key do dict da lista 'res'
    df = df[ (df['volume'] > volume_min) &  (df['close'] > preco_min) ]
    return df


df2 = dados_brapi()
df2 = df2[['stock', 'name', 'close', 'sector', 'volume']].sort_values(by='stock')
#retirar as que tem 11 no nome
# filter the rows that contain the substring
substring = '11'
filter = df2['stock'].str.contains(substring)
filtered_df = df2[~filter]
df2 = filtered_df

@st.cache_data
def lista():
    sfx = '.SA'
    acoess = df2['stock'].apply(lambda x: f"{x}{sfx}").values.tolist()
    return acoess

acoess = lista()


#today = datetime.datetime.strptime("2023-03-08", "%Y-%m-%d") #no formato que o yfinance exige
# today = datetime.datetime.today()
hoje = st.date_input('Data final')

# Widget de botão
execute_button = st.button("Executar")

if  hoje and execute_button:

    today = datetime.strptime(str(hoje), "%Y-%m-%d")

    # five_months_ago = today - relativedelta(months=5)
    # four_months_ago = today - relativedelta(months=4)
    # three_months_ago = today - relativedelta(months=3)
    # two_months_ago = today - relativedelta(months=2)
    # one_months_ago = today - relativedelta(months=1)

    # today = datetime.today()
    desired_dates = [today - timedelta(days=(32 * i)) for i in range(6)]
    # desired_dates = [today, one_months_ago, two_months_ago, three_months_ago, four_months_ago, five_months_ago]

    #today = datetime.datetime.strftime(today, '%Y-%m-%d') #precisou ser assim no online

    # """
    # conferir se as datas não são fim de semana.
    # Se for fim de semana, pega 2 dia anterior.
    # Se esse dia anterior passar para o mês anterior, então ao invés de diminuir 2 dia, soma 2 dia.
    # Somente se for fim de semana. Então:
    #     se for sábado 29, pega dados da quinta 27
    #     se for domingo 29, pega dados do sexta 27
    #     se for sábado 01, pega dados do segunda 03
    #     se for domingo 01, pega dados da terça 03
    # """



    for i, data in enumerate(desired_dates):
        if data.weekday() >= 5:  # se for sábado ou domingo
            nova_data = data - timedelta(days=2) #pega 2 dia antes
            if nova_data.month < data.month:  # se a nova data for do mês anterior
                nova_data = data + timedelta(days=2) #aí pega 2 dia depois        
            desired_dates[i] = nova_data

    # """
    # Conferir as datas calculadas jogando num dataframe com outra coluna com o número do dia da semana.
    # """
    dew = pd.DataFrame(desired_dates)
    dew = dew.rename( columns={0:'dias'} )
    dew['dias'] = pd.to_datetime(dew['dias']) #só pra garantir
    dew['semana'] = dew['dias'].dt.weekday


    # #intervalos para que bday_index fique maior que desired_dates
    # start_date = five_months_ago - relativedelta(days=3) #pra pegar 3 dias antes
    # end_date = today - datetime.timedelta(days=1) #data final é sempre hoje mesmo, não dá pra pegar mais dias à frente.
    # #Na verdade, nem a data de hoje vai ser pega, porque só tem dados de no máximo 1 dia antes.

    start_date = desired_dates[5] - relativedelta(days=3)
    end_date = today - timedelta(days=1)

    start_date.weekday()
    end_date.weekday()

         
    # Baixe os dados diários para o intervalo completo
    #baixa os dados também com o intervalo maior, pra garantir que as desired_dates estejam contidas
    @st.cache_data
    def baixa():
        data_yf = yf.download(acoess, start=start_date, end=end_date)['Adj Close'] #só a coluna que interessa
        return data_yf

    data_yf = baixa()
    data_yf.dropna(axis=1, inplace=True)

    # Verifique se as datas desejadas são dias úteis (dias da semana) e, se necessário, selecione as datas anteriores que sejam dias úteis
    #desired_dates = [today, one_months_ago, two_months_ago, three_months_ago, four_months_ago, five_months_ago]
    desired_dates_asof = []
    bday_index = pd.bdate_range(start=start_date, end=end_date, freq='C') # freq='C' para excluir feriados e fins de semana
    for d in desired_dates:
        if pd.to_datetime(d) in bday_index:
            desired_dates_asof.append(d)
        else:
            desired_dates_asof.append(bday_index[bday_index < pd.to_datetime(d)].max())



    # Selecione apenas as linhas correspondentes às datas que você deseja
    dfx = data_yf.loc[data_yf.index.isin(desired_dates_asof)]


    teste2 = dfx.copy()
    teste2.index = pd.to_datetime(teste2.index).strftime('%d-%m-%Y')
    teste2 = teste2.round(decimals = 2)
    df_pivot = teste2.T #para transpor

    #Jogando o nome das ações para uma coluna (só depois de transpor)
    df_pivot = df_pivot.reset_index() #ao resetar o index, o nome das ações fica em uma coluna 'index'.
    df_pivot = df_pivot.rename(columns={'index': 'ação'}) #renomeia essa coluna para 'ação'
    st.write(f"quantidade de colunas no dataframe: {df_pivot.shape[1]}") #vê a qtde de colunas. Se for menor que 6, vai dar erro
    print(df_pivot.shape[1])



    @st.cache_data
    def calcular_resultado(row):    
        varx5 = (row[1] / row[6]) - 1 #lembrando que o mês 5 está na coluna 1
        varx4 = (row[2] / row[6]) - 1 #lembrando que o mês 4 está na coluna 2
        varx3 = (row[3] / row[6]) - 1 #lembrando que o mês 3 está na coluna 3
        varx2 = (row[4] / row[6]) - 1 #lembrando que o mês 2 está na coluna 4
        varx1 = (row[5] / row[6]) - 1 #lembrando que o mês 1 está na coluna 5
        return (varx5*math.sqrt(5) + varx4*math.sqrt(4) + varx3*math.sqrt(3) + varx2*math.sqrt(2) + varx1*math.sqrt(1) ) / 8.382
        

    df_pivot['Ponderado'] = df_pivot.apply(lambda row: calcular_resultado(row), axis=1)
    # df_pivot.rename(columns={"resultado": "Ponderado"}, inplace = True)

    ##calculo do FR##
    df_pivot = df_pivot.sort_values(by='Ponderado', ignore_index=False) #tem que colocar em ordem crescente de ponderado primeiro
    df_pivot['C'] = np.arange(df_pivot.shape[0]) #cria uma coluna com o numero da linha
    df_pivot['FR'] = ( ( df_pivot.shape[0] - df_pivot['C']   ) /df_pivot.shape[0] ) * 100 #total de linhas - num da linha / total de linhas
    df_pivot = df_pivot.sort_values(by='FR', ascending=False, ignore_index=False) #classifica por FR em ordem decrescente, sem descartar o índice

    df_final = df_pivot[   (df_pivot['FR'] >= 90)]
    df_final

    #pra ter um dataframe só com o nome da ação e o valor de FFR
    new_df = df_pivot[['ação','FR']]
    new_df = new_df.query('FR >= 90')
    new_df.reset_index(inplace=True, drop=True) #drop joga fora a coluna com o index anterior
    new_df

    # Adicionando uma nova coluna com o preço mais recente para cada ação em new_df
    new_df['preço mais recente'] = new_df['ação'].apply(lambda x: dfx[x][-1])


    # """
    # Eu queria agora, conseguir rodar automaticamente com intervalos de 1 semana,
    # fazer um gráfico de colunas com o nome das ações new_df e os preços, e salvar tudo num gif

    # Pra isso eu posso usar yfdownload no intervalo maior,
    # aí vou mudando o valor de today semanalmente,
    # calculo as desired_dates de novo, filtro o dfx, calculo o FR e faço um gráfico com a última versão de new_df usando 
    # as colunas 'ação' e 'preço mais recente'
    # """



    st.write("data de hoje:", today)

    #ANALISAR O MACD DIÁRIO DAS AÇÕES SELECIONADAS, MOSTRANDO O PREÇO DELAS TAMBÉM
    # Lista de símbolos de ações
    lista = new_df['ação'].tolist()

    new_df = new_df.set_index('ação') #depois de gerar a lista
    new_df = new_df.round(decimals = 3)

    # Loop pelas ações na lista
    @st.cache_data
    def calcula_macd():
        for simbolo in enumerate(lista):
            # Obtém os dados do Yahoo Finance
            # global dadosx
            dadosx = yf.download(simbolo[1], start=start_date, end=end_date, progress=False)
            p = new_df.loc[simbolo[1], 'preço mais recente']        
        
            # Calcula o MACD
            macd = ta.trend.macd(dadosx['Adj Close'])
        
            # Verifica se o MACD está positivo e ascendente
            if macd[-1] > 0 and macd[-1] > macd[-2]:            
                st.write(f'{simbolo[1]}: MACD positivo ascendente, R${p}') #pra mostrar o preço também

    calcula_macd() #só pra escrever se tá ascendente

    #ÚLTIMO PENSAMENTO DO DIA:
    #SE AS AÇÕES ESTÃO BOAS NOS ÚLTIMOS 6 MESES, MESMO QUE ESTEJAM COM MACD DESCENDENTE, 
    #ELA TEM CHANCE SE DE RECUPERAR, OU SEJA, TALVEZ AS COM MACD DESCENDENTE SEJAM BOAS
    #OPORTUNIDADES DE COMPRA

    ##INCLUIR LINHA PARA FAZER UM DF COM AS AÇÕES COM MACD > 0 E OUTRO DF COM AÇÕES COM MACD < 0
    ##como fazer um gráfico só quando passar o mouse sobre, por exemplo, o nome da ação?

    #usando o go funciona
    # fig = go.Figure()
    # fig.add_trace(go.Candlestick(x=dadosx.index, open=dadosx['Open'], high=dadosx['High'], low=dadosx['Low'], close=dadosx['Close']) )
    # fig.update_layout(xaxis_rangeslider_visible=False)
    # st.plotly_chart(fig)

    # assim tambem funciona, com o cufflinks
    # fig = dadosx.iplot(asFigure=True, kind='candle', keys=["Open", "High", "Low", "Close"])
    # st.plotly_chart(fig)

    ##teste de gerar gráfico de uma ação selecionada
    choice = st.selectbox("escolha a ação", lista)
    #choice = "INBR32.SA"
    dadosx = yf.download(choice, start=start_date, end=end_date, progress=False)

    # print(cf.set_config_file.__doc__)
    # cf.getThemes()
    # cf.get_scales()
    # cf.colors.scales()
    dadosx.sort_index(ascending=True, inplace=True) #organiza pelo index, do mais antigo pro mais novo
    # dadosx

    cf.go_offline()
    cf.set_config_file(world_readable=True, theme='white') 
    pio.renderers.default = "notebook" # should change by looking into pio.renderers

    # AEEEE DEU CERTO
    qf = cf.QuantFig(dadosx, kind='candlestick', name=choice, title=choice)
    qf.add_bollinger_bands()
    qf.add_sma(name='sma20', color='red')
    qf.add_volume()
    # qf.add_resistance("2023-03-08") #ah, mas tem que passar a data na mão?
    fig = qf.iplot(asFigure=True, dimensions=(800, 400), up_color='green', down_color='red')

    #update_xaxes ou update_yaxes é do plotly, que gera a fig
    fig.update_xaxes(
        rangebreaks=[
            dict(bounds=["sat", "mon"]), #hide weekends
        ]
    )

    st.plotly_chart(fig)


    # #Fiz o mesmo com as ações que estão no TradingView
    # lista2 = ['CIEL3.SA','GMAT3.SA','PTBL3.SA','POSI3.SA','TTEN3.SA','MILS3.SA','TGMA3.SA','ITUB3.SA','RADL3.SA','PETR4.SA','KLBN3.SA','CPLE6.SA','ITSA4.SA','CMIG4.SA','B3SA3.SA','BBDC3.SA','GOAU4.SA','BBDC4.SA','ENAT3.SA','DIRR3.SA','ABCB4.SA','TRPL4.SA','CLSC4.SA','EGIE3.SA','CIEL3.SA','RANI3.SA','ALPA4.SA','AMZO34.SA','BBAS3.SA','VALE3.SA']
    # não deu certo usando o st.text_input porque ele não fica como lista.
    # Talvez se colocar elas como itens, mas vão ser muitos itens...
    # lista = list(lista2)
    # # Loop pelas ações na lista
    # for simbolo in enumerate(lista):
    #     # Obtém os dados do Yahoo Finance
    #     st.write(simbolo[1])
    #     dadosx = yf.download(simbolo[1], start=start_date, end=end_date, progress=False)

    #     # Calcula o MACD
    #     macd = ta.trend.macd(dadosx['Adj Close'])

    #     # Verifica se o MACD está positivo e ascendente
    #     if macd[-1] > 0 and macd[-1] > macd[-2]:
    #         st.write(f'{simbolo}: MACD positivo ascendente')
    # #coloquei enumerate pra poder imprimir o nome da ação antes de fazer o download pra procurar erros.
else:
    st.warning("Por favor, selecione uma data.")
