FROM python:3.10-slim

RUN apt-get update && \
    apt-get install -y build-essential wget libtool autoconf automake pkg-config && \
    wget https://github.com/ta-lib/ta-lib/releases/download/v0.6.4/ta-lib-0.6.4-src.tar.gz && \
    tar -xvzf ta-lib-0.6.4-src.tar.gz && \
    cd ta-lib && \
    ./configure --prefix=/usr && \
    make && \
    make install && \
    cd .. && \
    rm -rf ta-lib-0.6.4-src.tar.gz

# Ajuste para garantir que pip encontre a lib
ENV LD_LIBRARY_PATH=/usr/lib:$LD_LIBRARY_PATH
ENV CFLAGS="-I/usr/local/include"
ENV LDFLAGS="-L/usr/lib"
ENV TA_LIBRARY_PATH=$PREFIX/lib
ENV TA_INCLUDE_PATH=$PREFIX/include

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

# (Opcional) Remover ferramentas de build para reduzir o tamanho da imagem
RUN apt-get remove --purge -y build-essential wget libtool autoconf automake pkg-config && \
    apt-get autoremove -y && \
    apt-get clean

# Definir comando padrão
CMD ["python", "main.py"]


