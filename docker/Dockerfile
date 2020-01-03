FROM python:3.6-stretch

ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

RUN sed -i 's/main/main multiverse/' /etc/apt/sources.list
RUN apt-get update \
    && apt-get install -y libgdal-dev \
    git \
    gdal-bin \
    python3-gdal \
    zsh \
    python2.7-dev \
    python2.7-setuptools \
    && apt-get autoremove \
    && rm -rf /var/lib/apt /var/cache/apt 

RUN pip3 install --upgrade pip
RUN pip3 install GDAL==2.1.3 --global-option=build_ext --global-option="-I/usr/include/gdal"
RUN pip3 install shapely \
    numpy \
    pandas \
    pyyaml \
    bokeh \
    folium \
    matplotlib \
    pscript \
    && rm -rf /.cache/pip

RUN pip3 install --upgrade google-api-python-client \
    oauth2client \
    pyOpenSSL>=0.11 \
    earthengine-api \
    && rm -rf /.cache/pip


RUN pip install --no-cache-dir -U crcmod gsutil && rm -rf /.cache/pip

RUN apt-get update \
    && apt-get install -y rsync \
    && apt-get autoremove \
    && rm -rf /var/lib/apt /var/cache/apt 

CMD /bin/bash
