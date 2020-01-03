import numpy as np
import pandas as pd
import datetime
from glob import glob 
import os

# Bokeh libraries
from bokeh.io import output_file, show
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, HoverTool,CustomJS
from bokeh.tile_providers import get_provider, Vendors
from bokeh.models.widgets import Tabs, Panel

import matplotlib
from matplotlib import cm
import re

def natural_sort(l): 
    convert = lambda text: int(text) if text.isdigit() else text.lower() 
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ] 
    return sorted(l, key = alphanum_key)

def get_data_list(wd='/contents/output', collection='sample'):
    wd = '%s/%s'%(wd,collection)
    datalist = sorted(glob('%s/*long*.csv'%wd))
    return(datalist)

def parse_name(filename):
    return(str('_').join(os.path.basename(filename).split('_')[:-4]))

def get_collection_data(collection='sample'):
    return(pd.read_csv(natural_sort(glob('collections/%s*.csv'%collection))[-1]))

def get_data(datalist):
    list_types = []
    for filename in datalist:
        list_types.append(parse_name(filename))
    data = {k:pd.read_csv(v)[['location','img_date']] for k,v in zip(list_types,datalist)}
    return(data)

def generate_colormap(n):
    cmap = cm.get_cmap('viridis', n)
    cmap = [matplotlib.colors.rgb2hex(cmap(i)[:3]) for i in range(n)]
    return(cmap)

def summarize_data(data):
    EARLIEST_DATE = '1979-01-01'
    today = datetime.datetime.today()
    datanames = list(data.keys())
    scales = np.linspace(0,1,len(datanames)+1)
    summary_ds = pd.DataFrame(pd.date_range(EARLIEST_DATE,today), columns=['img_date'])
    for name in datanames:
        summary_ds[name] = summary_ds['img_date'].isin(data[name]['img_date']).astype('int')
        cname = '%s_cs'%name
        #add cumulative sum estimates
        summary_ds[cname] = np.cumsum(summary_ds[name])
    #rescale the names and add bottom bounds
    for i in range(len(datanames)):
        summary_ds[datanames[i]] = np.clip(summary_ds[datanames[i]],scales[i],scales[i+1])
        zeroname = '%s_zero'%datanames[i]
        summary_ds[zeroname] = np.ones(len(summary_ds))*scales[i]
    summary_ds['xax'] = np.zeros(len(summary_ds))
    return(summary_ds)

def merc(lat, lon):
    r_major = 6378137.000
    x = r_major * np.radians(lon)
    scale = x/lon
    y = 180.0/np.pi * np.log(np.tan(np.pi/4.0 + lat * (np.pi/180.0)/2.0)) * scale
    return (y, x)

def build_map(data, collection):
    collection = get_collection_data(collection)
    ids = np.unique(collection.PlotKey)
    dkeys = list(data.keys())
    for k in dkeys:
        colname = '%s_count'%k
        collection[colname] = np.array([np.sum(data[k].location==i) for i in ids])
    center_x = np.mean(collection.Latitude) 
    center_y = np.mean(collection.Longitude) 
    mlat,mlon = merc(collection.Latitude,collection.Longitude)
    collection['mLatitude'],collection['mLongitude'] = mlat, mlon
    X_BOUNDS,Y_BOUNDS = 2000000,100000
    x_range = (np.mean(mlon)-X_BOUNDS, np.mean(mlon)+X_BOUNDS)
    y_range = (np.mean(mlat)-Y_BOUNDS, np.mean(mlat)+Y_BOUNDS)
    tooltips = [("Plot Key","@PlotKey"), ("(Lon,Lat)","(@Longitude,@Latitude)")]
    tooltips.extend([("%s Acq. Count"%dk,"@%s_count"%dk) for dk in dkeys])
    tile_provider = get_provider(Vendors.CARTODBPOSITRON)
    # range bounds supplied in web mercator coordinates
    source = ColumnDataSource(collection)
    bmap = figure(x_range=x_range, y_range=y_range,\
               x_axis_type="mercator", y_axis_type="mercator",\
               tooltips=tooltips)
    bmap.add_tile(tile_provider)
    bmap.circle(x='mLongitude',y='mLatitude',size=10, alpha=0.7, source=source)
    bmap.hover.point_policy = 'follow_mouse'
    return(bmap)

def build_cumulative_fig(summary_ds, datanames):
    n = len(datanames)
    source = ColumnDataSource(summary_ds)
    cmap = generate_colormap(n)

    clmfig = figure(x_axis_type='datetime',\
                 plot_height=300, plot_width=800,\
                 title='Cumulative Acquisition Summary',\
                 x_axis_label='Date', y_axis_label='Total Acquisitions',\
                 toolbar_location='right')
    lines = []
    for name,color in zip(datanames,cmap):
        l = clmfig.line('img_date', '%s_cs'%name, color=color,\
                    source=source, legend_label=name)
        lines.append(l)
        htool = HoverTool(
            renderers=[l],\
            tooltips=[('Date','@img_date{%Y-%m-%d}'),('Acq. to Date','@%s_cs'%name)],\
            formatters={'img_date': 'datetime',})
        clmfig.add_tools(htool)
    legend = clmfig.legend[0]
    csnames = ['%s_cs'%name for name in datanames]
    ranges = [(np.min(summary_ds[d]), np.max(summary_ds[d])) for d in csnames] 
    clmfig.legend.location = 'top_left' 
    clmfig.legend.click_policy='hide'
    callback=CustomJS(args=dict(fig=clmfig,\
                                lines=lines,\
                                datanames=csnames,\
                                ranges=ranges),\
                      code='''
                      var max = 0;
                      var min = -30;
                      for (i=0;i<datanames.length;i++){
                        if(lines[i].attributes.visible){
                            if (ranges[i][0]<min){
                                min = ranges[i][0];
                            }
                            if (ranges[i][1]>max){
                                max = ranges[i][1];
                            }
                        }
                      }
                      fig.y_range.start = min
                      fig.y_range.end = max
                      ''')
    for item in legend.items:
        item.renderers[0].js_on_change('visible',callback)
    #xline = clmfig.line('img_date', 'xax', source=source,color=None)
    #datetool = HoverTool(
    #    renderers=[xline],
    #    tooltips=[('Date','@img_date{%y-%m-%d}'),],\
    #    formatters={'img_date': 'datetime',},\
    #    # display a tooltip whenever the cursor is vertically in line with a glyph
    #    mode='vline')
    #clmfig.add_tools(datetool)
    return(clmfig)

def build_acquisition_fig(summary_ds,datanames):
    source = ColumnDataSource(summary_ds)
    n = len(datanames)
    cmap = generate_colormap(n)
    scales = np.linspace(0,1,n+1)
    #tooltips = [('img_date', '@img_date')]
    TOOLS = "xpan,xwheel_zoom,box_zoom,reset,save"
    acqfig = figure(x_axis_type='datetime', tools=TOOLS,\
                 plot_height=300, plot_width=600,\
                 title='Date Acquisition Summary',\
                 x_axis_label='Acquisition Date', y_axis_label=None,\
                 toolbar_location='right')
    for i in range(n):
        acqfig.vbar('img_date', top=datanames[i],bottom='%s_zero'%datanames[i],width=1,\
                 color=cmap[i],
                 source=source)
    #htool = HoverTool(
    #    tooltips=[('date','@img_date{%y-%m-%d}'),],\
    #    formatters={'img_date': 'datetime',},\
    #    # display a tooltip whenever the cursor is vertically in line with a glyph
    #    mode='vline')
    #acqfig.add_tools(htool)
    ytics = scales[:-1]+(1/(n*2))
    acqfig.yaxis.ticker = ytics
    tick_labels = datanames
    acqfig.yaxis.major_label_overrides = dict(zip(ytics, tick_labels))
    return(acqfig)

def build_figs(data, collection):
    summary_ds = summarize_data(data)
    datanames = list(data.keys())
    clmfig = build_cumulative_fig(summary_ds, datanames)
    acqfig = build_acquisition_fig(summary_ds, datanames)
    mapfig = build_map(data, collection)
    return(mapfig,acqfig,clmfig)

def generate_visualization(wd='/contents/output', collection='sample'):
    fileout = '%s/%s_report.html'%(wd,collection)
    output_file(fileout, title='DACQRE Summary Report')
    dl = get_data_list(wd, collection)
    data = get_data(dl)
    mapfig, acqfig, clmfig = build_figs(data, collection)
    map_panel = Panel(child=mapfig, title='Map of Collection Points')
    date_panel = Panel(child=acqfig, title='Acquistition by Date Summary')
    clm_panel = Panel(child=clmfig, title='Cumulative Acquisition Summary')
    tabs = Tabs(tabs=[map_panel, date_panel, clm_panel]) 
    print('Wrote data summary to %s!'%fileout)
    return(tabs)

if __name__ == "__main__":
    wd = '/contents/output'
    collection = 'sample'
    tabs = generate_visualization(wd=wd, collection=collection)
    show(tabs)
