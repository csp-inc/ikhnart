FROM nvidia/cuda:8.0-cudnn6-devel-ubuntu16.04

ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

RUN apt-get update && apt-get install -y software-properties-common 
RUN add-apt-repository ppa:deadsnakes/ppa && add-apt-repository ppa:jonathonf/python-3.6
RUN apt-get update && apt-get install -y python3.6-dev python3.6-venv \
    wget git graphviz libgraphviz-dev
RUN wget https://bootstrap.pypa.io/get-pip.py
RUN python3.6 get-pip.py
RUN ln -s /usr/bin/python3.6 /usr/local/bin/python3
RUN add-apt-repository ppa:ubuntugis/ubuntugis-unstable 

RUN apt-get update \
    && apt-get install -y libgdal-dev libevent-dev\
       libgdal1i libgdal-dev python-gdal\
       git \
    && apt-get autoremove \
    && rm -rf /var/lib/apt /var/cache/apt 

ENV LANG C.UTF-8

RUN pip install psycopg2 owslib --upgrade
RUN pip install tensorflow-gpu==1.4.0 \
    keras==2.0.8 \
    gdal==2.2.2 \
    pygdal==2.2.2.3\
    sklearn \
    scikit-image \
    tensorboard \
    rasterio \
    mapboxcli \ 
    kulc \
    keras-vis \
    jupyter \
    folium \ 
    pandas \
    tqdm \
    && rm -rf /.cache/pip

RUN mkdir -p $(jupyter --data-dir)/nbextensions 
RUN cd $(jupyter --data-dir)/nbextensions && \
    git clone https://github.com/lambdalisue/jupyter-vim-binding vim_binding && \
    jupyter nbextension enable vim_binding/vim_binding
