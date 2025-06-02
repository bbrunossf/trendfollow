FROM python:3.10-slim

RUN apt-get update && \
    apt-get install -y build-essential wget libtool autoconf automake pkg-config && \
    wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz && \
    tar -xvzf ta-lib-0.4.0-src.tar.gz && \
    cd ta-lib && \
    ./configure --prefix=/usr/local && \
    make && \
    make install && \
    cd .. && \
    rm -rf ta-lib ta-lib-0.4.0-src.tar.gz

# Ajuste para garantir que pip encontre a lib
ENV LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH
ENV CFLAGS="-I/usr/local/include"
ENV LDFLAGS="-L/usr/local/lib"

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

# (Opcional) Remover ferramentas de build para reduzir o tamanho da imagem
RUN apt-get remove --purge -y build-essential wget libtool autoconf automake pkg-config && \
    apt-get autoremove -y && \
    apt-get clean

# Definir comando padrão
CMD ["python", "main.py"]


