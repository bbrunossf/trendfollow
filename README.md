# Trend following de ativos na B3

## Descrição do projeto
Este projeto tem como objetivo criar uma aplicação web para listar ativos em alta com potencial para investir. As principais bibliotecas usadas foram yfinance, pandas, cufflinks e streamlit.

## Objetivo

Com tantas opções de investimento, fica difícil avaliar as melhores opções, de acordo com a estratégia de cada investidor.  
Este projeto ajuda a avaliar ativos que estejam com boa tendência de alta considerando um histórico de 6 meses, e perspectivas de crescimento.


## Tecnologias Utilizadas

Este projeto foi elaborado usando Python.  
As principais bibliotecas utilizadas foram:  
- Streamlit, para a interface web;
- Yfinance e API Brapi, para obter os dados dos ativos;
- Pandas, para manipulação dos dados;
- Cufflinks, para criação dos gráficos e indicadores.

## Coleta de Dados

Inicialmente, foram definidos os seguintes limites:
- somente ativos com volume mínimo de negociação diária de R$200.000,00 (visando garantir uma boa liquidez);
- somente ativos com preço negociado acima de R$3,00 (visando evitar altas volatilidades - uma variação de 10 centavos em um ativo com preço R$2,00 equivale a uma variação de 5%!);
- somente ativos sem o código '11' (fundos de índices).  

A API Brapi permite listar todos os ativos da B3, e foi criado um dataframe inicial com os ativos que atendam aos limites definidos anteriormente;

## Estratégia adotada
A estratégia adotada consiste em analisar o preço dos ativos nos últimos 6 meses a partir de uma data selecionada, ponderando empiricamente as variações mensais.  

Nesta etapa, o maior desafio foi garantir que, dentro do intervalo determinado a partir da data selecionada, as 6 datas anteriores (uma por mês) fossem realmente de dias úteis, com negociações na Bolsa.  

## Solução para dias úteis
A solução foi verificar se houve negociação do ativo mais negociado na B3 e com maior representação no índice BOVESPA: A VALE. Caso o resultado seja nulo, outra data (antes ou depois) é testada, até obter um conjunto válido.


## Manipulação de Dados

### Transformações iniciais, Cache e redução de execuções
Para usar a biblioteca yfinance, é preciso incluir o sufixo '.SA' no nome dos ativos retornados pela API da Brapi;  

Foram selecionadas as seguintes colunas dos dados retornados pela API da Brapi: 'stock' (símbolo do ativo), 'name' (nome da empresa), 'close' (preço de fechamento), 'sector' (setor da empresa), 'volume' (volume diário negociado, em R$). Como a biblioteca Streamlit executa novamente o código inteiro a cada iteração do usuário, foi criada uma função com o atributo cache para reduzir a execução desnecessária (os nomes dos ativos não mudam);  

Para considerar a variação da quantidade de dias por mês, foi utilizado o valor de 32 dias, e calculadas 6 datas a partir da data selecionada pelo usuário;  

As datas calculadas são então testadas, se houve negociação do ativo VALE3.SA, pesquisando com a biblioteca yfinance o preço de fechamento ajustado do dia. Caso negativo, uma nova data é testada, até obter o conjunto de 6 observações;  

O próximo passo foi obter os valores diários dos ativos filtrados, considerando os extremos do intervalo definido, e utilizando a biblioteca yfinance, filtrando somente as datas desejadas (novamente, com a criação de uma função, utilizando o atributo cache, já que os preços registrados não mudam);   

### Ponderação e classificação dos ativos
O fator de ponderação foi implementado em uma função e aplicado para todo o dataframe, salvando o valor em uma nova coluna;  

A etapa seguinte da manipulação de dados consiste em classificar os ativos pelo fator de ponderação calculado, e selecionados somente aqueles com valor maior ou igual a 90, retornando uma tabela com o nome dos ativos e o último preço de fechamento praticado;  

A última etapa consiste em calcular a ascendência ou descendência da média móvel de 20 períodos dos ativos selecionados.


## Criação de Gráficos e indicadores

A partir do ativo filtrado selecionado na interface web, é criado o gráfico de candles utilizando a biblioteca cufflinks. Esta biblioteca já possui métodos específicos para criação de gráfico de candles e indicadores gráficos.  

Foram inseridos os seguintes indicadores gráficos:
- Bandas de Bollinger;
- médias móveis de 20 períodos;
- volume de negociação.

Além do fator de ponderação, o gráfico do ativo contribui para análise, ao verificar os indicadores gráficos e validar a tendência observada.


## Interface Web

A opção pela biblioteca Streamlit é a facilidade de uso na criação do código, e a possibilidade de hospedar a aplicação no host da própria biblioteca. Embora não seja recomendada para uso em produção, Streamlit permite a criação rápida e funcional de um protótipo para aplicações pequenas.  

A interface possui os seguintes campos para operação pelo usuário:
- Definição da data final do período a ser analisado;
- Botão 'executar', para disparar o início da obtenção e manipulação dos dados;
- menu dropdown com os ativos filtrados pelo fator de ponderação, para posterior apresentação do gráfico de candles. A cada novo ativo selecionado, o gráfico é automaticamente atualizado.

## Exemplo de uso (Não é recomendação de investimento)  

Considerando a data de 01/06/2024 (um sábado), o ativo com maior fator de ponderação é o **BIOM3.SA**, com preço de R$17,50.  
O cálculo do MACD mostra uma curva positiva ascendente, e o gráfico de candles mostra uma queda do preço do ativo no período de 02/05 a 24/05, com boa retomada do crescimento até a data atual (somente candles positivos), ultrapassando a média de 20 períodos, reforçando a probabilidade de tendência de alta.  

Observe que não é preciso selecionar uma data útil, pois o código já busca o dia útil mais próximo.

## Conclusão

Este projeto demonstra como é possível utilizar dados financeiros e ferramentas de análise de dados para identificar ativos com potencial de alta na B3. A interface web facilita a interação do usuário com os dados, proporcionando uma ferramenta alternativa prática para investidores.

## Código-fonte
O código-fonte completo está disponível em [https://github.com/bbrunossf/trendfollow].  
A aplicação está hospedada em [https://bbrunossf-trendfollow-consolidado1-xsxei5.streamlit.app/].
A imagem renderizada do jupyter notebook está em [https://nbviewer.org/github/bbrunossf/trendfollow/blob/master/trend_follow.ipynb]
