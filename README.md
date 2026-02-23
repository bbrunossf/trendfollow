# Trend following de ativos na B3

## Descrição do projeto
Este projeto tem como objetivo criar uma aplicação web para listar ativos em alta com potencial para investir. As principais bibliotecas usadas foram yfinance, pandas, e FastAPI, entre outros.

## Objetivo

Com tantas opções de investimento, fica difícil avaliar as melhores opções, de acordo com a estratégia de cada investidor.  
Este projeto ajuda a avaliar ativos que estejam com boa tendência de alta considerando um histórico de 6 meses, e perspectivas de crescimento.  
Além dessa estratégia, são inseridos diversos indicadores para reforçar ou refutar a análise, fornecendo ao usuário ferramentas para decidir pelos ativos, bem como o ponto de saída das operações (stop gain e stop loss).  


## Tecnologias Utilizadas

Este projeto inicialmente foi elaborado usando Python, e nessa versão foi refatorado para usar uma interface web com js mínimo.  
As principais bibliotecas utilizadas foram:  
- FastAPI, para a interface web;
- Yfinance e API Brapi, para obter os dados dos ativos;
- Pandas, para manipulação dos dados;
- scripts em javascript para renderização dos gráficos e indicadores.

## Coleta de Dados

Inicialmente, foram definidos os seguintes limites:
- somente ativos com volume mínimo de negociação diária de R$200.000,00 (visando garantir uma boa liquidez);
- somente ativos com preço negociado acima de R$3,00 (visando evitar altas volatilidades - uma variação de 10 centavos em um ativo com preço R$2,00 equivale a uma variação de 5%!);
- somente ativos sem o código '11' e '32' (fundos de índices).  
Todos esses critérios são definidos em variáveis no arquivo config.py, permitindo fácil alteração

A API Brapi permite listar todos os ativos da B3, e foi criado um dataframe inicial com os ativos que atendam aos limites definidos anteriormente;
**NOTA:** Na versão atualizada da API da Brapi, o endpoint de consulta com retorno dos ativos e dados iniciais (como último preço de fechamento, volume, etc) mudou. Outra grande mudança é que agora existem outros endpoints para consulta de dados históricos de ativos, assim como no yfinance. A versão gratuita da API tem um bom limite de consultas mensais, e pode ser uma vantagem migrar o código no futuro para não depender mais da yfinance.

## Estratégia adotada
A estratégia adotada consiste em analisar o preço dos ativos nos últimos 6 meses a partir de uma data selecionada, ponderando empiricamente as variações mensais, dando um peso maior para as variações positivas de preços nos períodos mais antigos.  

## Solução para dias úteis
Na versão anterior o teste para verificar se as datas selecionadas foram dias úteis (ou seja, se houve negociação de ativos nesse dia) foi testar separadamente cada data, fazendo uma consulta de preços pelo ativo 'VALE3.SA', que tem uma grande representação no índice BOVESPA. A ideia é que a probabilidade de ser um dia útil sem negociações desse ativo é muito pequena.  
Nessa versão, é feita a consulta no período determinado, e depois as datas são testadas, simplesmente verificando se a respectiva coluna está totalmente vazia, usando a data do dia anterior caso positivo, até encontrar uma nova data válida. Esse processo reduz a necessidade de diversas consultas usando o yfinance, fazendo uma única consulta e depois manipulando o dataframe.  


## Manipulação de Dados

### Transformações iniciais, Cache e redução de execuções
Para usar a biblioteca yfinance, é preciso incluir o sufixo '.SA' no nome dos ativos retornados pela API da Brapi;  

Foram selecionadas as seguintes colunas dos dados retornados pela API da Brapi: 'stock' (símbolo do ativo), 'name' (nome da empresa), 'close' (preço de fechamento), 'sector' (setor da empresa), 'volume' (volume diário negociado, em R$).  

O próximo passo foi obter os valores diários dos ativos filtrados, considerando os extremos do intervalo definido, e utilizando a biblioteca yfinance, e depois fazendo 'snapshots' somente com as datas desejadas. Esses valores são usados na construção de um gráfico de linhas inicial que mostra a evolução dos preços dos ativos filtrados posteriormente pelo índice de força relativa.  

### Ponderação e classificação dos ativos
Nessa nova versão, foram criadas funções separadas para o cálculo do 'scoring' e do 'ranking', ou seja, calcular o índice de força relativa, e depois ordenar os ativos com base nesse indicador, selecionando aqueles com FR > min_score definido pelo usuário.  

## Criação de Gráficos e indicadores

A partir do ativo filtrado selecionado na interface web, é criado o gráfico de candles com a exibição dos indicadores. Nessa versão, optou-se por  não utilizar bibliotecas externas, considerando que algumas (em particular a biblioteca 'ta') são difíceis de instalar e manter, e o benefício de usá-las não é significativo, podendo ser criadas funções mais básicas para o cálculo dos indicadores.   

Foram criadas funções para calcular os seguintes indicadores gráficos:
- Bandas de Bollinger;
- médias móveis de 20 períodos;
- volume de negociação;
- indicador MACD;
- indicador ATR.

Além do fator de ponderação, o gráfico do ativo contribui para análise, ao verificar os indicadores gráficos e validar a tendência observada.

## Interface Web

<descrever a nova interface>  

## Estrutura de diretórios e arquivos, definição de responsabilidades e backend/frontend

## Conclusão

Este projeto demonstra como é possível utilizar dados financeiros e ferramentas de análise de dados para identificar ativos com potencial de alta na B3. A interface web facilita a interação do usuário com os dados, proporcionando uma ferramenta alternativa prática para investidores.

## Código-fonte
O código-fonte completo está disponível em <em atualização> .  
A aplicação está hospedada em <em atualização>.  
A imagem renderizada do jupyter notebook está em <em atualização>
