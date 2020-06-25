FROM tensorflow/tensorflow:2.0.0-py3-jupyter

LABEL org.label-schema.license="CSP-1.0" \
	org.label-schema.vcs-url="https://gitlab.com/tonychang" \
	org.label-schema.vendor="Conservation Science Partners" \
	maintainer="Tony Chang <tony@csp-inc.org>"
   
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

RUN apt-get update \
    && apt-get install -y wget \
       git \
       geos++-dev \
       libproj-dev \
    && apt-get autoremove \
    && rm -rf /var/lib/apt /var/cache/apt 

RUN pip install --upgrade pip \
    keras \
    scikit-image \
    scikit-learn \
    bokeh \
    pandas \
    numpy \ 
    geopy \
    earthengine-api \
    matplotlib \
    rasterio \
    dask \
    xarray \
    intake \
    pyviz \
    mapboxcli \ 
    kulc \
    geopandas \
    descartes \
    folium \
    fiona \
    cython \
    && rm -rf /.cache/pip

#RUN pip install geoplot

#RUN pip install git+https://github.com/SciTools/cartopy 
#RUN pip install geoplot
#RUN git clone https://github.com/SciTools/cartopy && python cartopy/setup.py install \

RUN mkdir -p $(jupyter --data-dir)/nbextensions 
RUN cd $(jupyter --data-dir)/nbextensions && \
    git clone https://github.com/lambdalisue/jupyter-vim-binding vim_binding && \
    jupyter nbextension enable vim_binding/vim_binding

