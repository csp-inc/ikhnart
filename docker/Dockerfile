FROM tensorflow/tensorflow:2.0.0-gpu-py3-jupyter

LABEL org.label-schema.license="CSP-1.0" \
	org.label-schema.vcs-url="https://gitlab.com/tonychang" \
	org.label-schema.vendor="Conservation Science Partners" \
	maintainer="Tony Chang <tony@csp-inc.org>"
   
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

RUN apt-get update \
    && wget \
       git \
    && apt-get autoremove \
    && rm -rf /var/lib/apt /var/cache/apt 

RUN pip install keras \
    scikit-image \
    bokeh \
    pandas \
    numpy \ 
    matplotlib \
    rasterio \
    mapboxcli \ 
    kulc \
    geopandas \
    descartes \
    folium \
    fiona \
    rtree \
    && rm -rf /.cache/pip

RUN mkdir -p $(jupyter --data-dir)/nbextensions 
RUN cd $(jupyter --data-dir)/nbextensions && \
    git clone https://github.com/lambdalisue/jupyter-vim-binding vim_binding && \
    jupyter nbextension enable vim_binding/vim_binding

