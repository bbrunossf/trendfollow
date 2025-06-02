# Imagem base leve com Python
FROM python:3.10-slim

# Instalar dependências de sistema necessárias para compilar o TA-Lib
RUN apt-get update && \
    apt-get install -y build-essential wget libtool autoconf automake pkg-config && \
    wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz && \
    tar -xvzf ta-lib-0.4.0-src.tar.gz && \
    cd ta-lib && \
    ./configure --prefix=/usr && \
    make && \
    make install && \
    cd .. && \
    rm -rf ta-lib ta-lib-0.4.0-src.tar.gz && \
    apt-get remove --purge -y wget build-essential libtool autoconf automake pkg-config && \
    apt-get autoremove -y && \
    apt-get clean

# Definir diretório de trabalho
WORKDIR /app

# Copiar arquivos do projeto para o contêiner
COPY . .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Definir comando para rodar a aplicação
CMD ["python", "main.py"]
