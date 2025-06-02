FROM python:3.10-slim

# Instalar dependências de sistema para compilação e TA-Lib
RUN apt-get update && \
    apt-get install -y build-essential wget libtool autoconf automake pkg-config && \
    wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz && \
    tar -xvzf ta-lib-0.4.0-src.tar.gz && \
    cd ta-lib && \
    ./configure --prefix=/usr && \
    make && \
    make install && \
    cd .. && \
    rm -rf ta-lib ta-lib-0.4.0-src.tar.gz

# Definir diretório de trabalho
WORKDIR /app

# Copiar o código do projeto
COPY . .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# (Opcional) Remover ferramentas de build para reduzir o tamanho da imagem
RUN apt-get remove --purge -y build-essential wget libtool autoconf automake pkg-config && \
    apt-get autoremove -y && \
    apt-get clean

# Definir comando padrão
CMD ["python", "main.py"]
