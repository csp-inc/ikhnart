#Mapdisplay: Display ee.Features and ee.Images using folium.
import folium
import ee
from shapely.geometry import Point, Polygon
from datetime import datetime
import geopandas as gpd
import numpy as np

ee.Initialize()
EE_TILES = 'https://earthengine.googleapis.com/map/{mapid}/{{z}}/{{x}}/{{y}}?token={token}'

def Mapdisplay(center, dicc, Tiles="OpensTreetMap",zoom_start=10):
    '''
    :param center: Center of the map (Latitude and Longitude).
    :param dicc: Earth Engine Geometries or Tiles dictionary
    :param Tiles: Mapbox Bright,Mapbox Control Room,Stamen Terrain,Stamen Toner,stamenwatercolor,cartodbpositron.
    :zoom_start: Initial zoom level for the map.
    :return: A folium.Map object.
    '''
    mapViz = folium.Map(location=center,tiles=Tiles, zoom_start=zoom_start)
    for k,v in dicc.items():
        if ee.image.Image in [type(x) for x in v.values()]:
            folium.TileLayer(\
            tiles = EE_TILES.format(**v),\
            attr  = 'Google Earth Engine',\
            overlay =True,\
            name  = k\
                    ).add_to(mapViz)
        else:
            folium.GeoJson(\
            data = v,\
            name = k\
            ).add_to(mapViz)
        mapViz.add_child(folium.LayerControl())
    return mapViz

def plotDot(point,this_map):
    '''input: series that contains a numeric named latitude and a numeric named longitude
    this function creates a CircleMarker and adds it to your this_map'''
    folium.CircleMarker(location=[point.Latitude, point.Longitude],
    radius=2,
    weight=0).add_to(this_map)

def random_point_in_shp(shp):
    within = False
    while not within:
        x = np.random.uniform(shp.bounds.minx, shp.bounds.maxx)
        y = np.random.uniform(shp.bounds.miny, shp.bounds.maxy)
        within = shp.contains(Point(x, y)).values[0]
    return Point(x,y)

def get_bound_points(geometry):
    xmin, ymin, xmax, ymax = geometry.bounds
    pnts = [(xmin, ymin),\
        (xmin, ymax),\
        (xmax, ymax),\
        (xmax, ymin),\
        (xmin, ymin)]
    return pnts

def convert_datelist_to_string(datelist):
    return f'%s-%02d-%02d'%(datelist[0],datelist[1],datelist[2])

def generate_ee_points(df, idname='id'):
    '''input: dataframe of points and buffer size in meters,
    returns: ee.FeatureCollection of box buffers and GeoDataFrame 
    with original points as centroid'''
    features=[]
    ids = []
    for index, row in df.iterrows():
        f = ee.Geometry.Point(row['geometry'].x,row['geometry'].y)
        # Define feature with a geometry and 'name' field from the dataframe
        feature = ee.Feature(f,{'id':ee.String(row[idname])})
        features.append(feature)
    fc = ee.FeatureCollection(features)
    return fc

def generate_box_buffer(df, buffersize=60,idname='id'):
    '''input: dataframe of points and buffer size in meters,
    returns: ee.FeatureCollection of box buffers and GeoDataFrame 
    with original points as centroid'''
    features=[]
    ids = []
    for index, row in df.iterrows():
        f = ee.Geometry.Point(row['geometry'].x,row['geometry'].y).buffer(buffersize).bounds()
        # Define feature with a geometry and 'name' field from the dataframe
        feature = ee.Feature(f,{'id':ee.String(row[idname])})
        features.append(feature)
    fc_boxes = ee.FeatureCollection(features)
    #For plotting
    fbox = fc_boxes.getInfo()['features']
    i = []
    g = []
    for f in fbox:
        i.append(f['properties']['id'])
        g.append(Polygon(f['geometry']['coordinates'][0]))
    box = gpd.GeoDataFrame({'id':i, 'geometry':g}, crs={'init':'epsg:4326'})    
    return {'ee_fc':fc_boxes, 'box_df':box}

### added functions from Chimera v2.0.0
def add_cloud(image,cloud_threshold=20):
    '''
    Input:
        image : <ee.Image>
    Output:
        finalimage : <ee.Image> with added cloudscore band named 'cloud'
    '''
    cloudscore = ee.Algorithms.Landsat.simpleCloudScore(image)
    mask = cloudscore.select(['cloud']).lte(cloud_threshold)
    cloudimage = image.addBands(cloudscore)
    finalimage = cloudimage.updateMask(mask)
    return(finalimage)

def trimEdges(image):
     lsgeom = ee.Geometry(image.geometry())
     buffgeom = ee.Geometry(lsgeom.buffer(-9000))
     return(image.clipToBoundsAndScale(buffgeom,scale=30))

def cloud_filter(im_collection, max_cloud_thr=31, verbose=False):
    '''
    Input:
        im_collection: <ee.ImageCollection object> from Sentinel-2 collection
        max_cloud_thr: <int>
    Output:
        return <ee.ImageCollection object> 
    '''
    filtered_sentinel_ic = im_collection.filterMetadata('CLOUDY_PIXEL_PERCENTAGE', 'less_than',\
        int(max_cloud_thr))
    num_images = filtered_sentinel_ic.size().getInfo()
    if num_images == 0:
        print(f'WARNING! No SENTINEL images within {max_cloud_thr} cloud threshold in time window.')
    if verbose:
        print(f'Found {num_images} SENTINEL image(s) with below {max_cloud_thr} percent cloud cover.\n')
        datelist = [ee.Date(im).format('YYYY-MM-dd').getInfo() \
                for im in filtered_sentinel_ic.aggregate_array('system:time_start').getInfo()]
        for i,date in enumerate(datelist):
            print(f'Image {i+1}: {date}')
        print('\n')
        if num_images >=0:
           print(f'Collected {num_images} SENTINEL image(s) data.\n') 
        else:
           print(f'Warning! Increase cloud threshold, no SENTINEL images found.') 
        
    return(filtered_sentinel_ic)

def get_sentinel_data(bounds, daterange, max_cloud_thr=None, SR=False, \
    bands=['B4','B3','B2'], aggregation='min', verbose=False):
    '''
    Input:
        bounds: <ee.bounds object> 
        daterange: <ee.DateRange object>
        max_cloud_thr: <int>
        SR: <bool>
        bands: <list> bands to select
        aggregation: <str> method to aggregate images together
        verbose: <bool> 

    Output:
        returns <ee.ImageCollection> of COPERNICUS/S2 or S2_SR with data filtered by bounds, daterange,
        and CLOUDY_PIXEL_PERCENTAGE below threshhold.
    '''
    if SR:
        s_collection = ee.ImageCollection('COPERNICUS/S2_SR')
    else:
        s_collection = ee.ImageCollection('COPERNICUS/S2')
    if max_cloud_thr is None:
        max_cloud_thr = 100
    sentinel_collection = s_collection.filterBounds(bounds).filterDate(daterange).select(bands)
    collection_size = sentinel_collection.size().getInfo()
    start = datetime.utcfromtimestamp(daterange.getInfo()['dates'][0]/1000).date()
    end = datetime.utcfromtimestamp(daterange.getInfo()['dates'][1]/1000).date() 
    if collection_size == 0:
        print(f'No SENTINEL data in dates between {start} and {end}.')
        return []
    else:
        if verbose:
            print(f'Found {collection_size} SENTINEL image(s) between {start} and {end}.')
        filtered_sentinel = cloud_filter(sentinel_collection, max_cloud_thr, verbose=verbose)
        if aggregation == 'min':
            return filtered_sentinel.min()
        elif aggregation == 'median':
            return filtered_sentinel.median()
        else:
            return filtered_sentinel.mean()

def create_date_range(datelist,monthwindow=2):
    '''
    Input:
        datelist : <list or tuple> of date in (YY,MM,DD) format
        monthwindow : <int> month before and after <datelist> to search around
    Output: 
        returns Earth Engine DateRange object.
    '''
    datecenter = ee.Date.fromYMD(datelist[0],datelist[1],datelist[2])
    window = ee.DateRange(datecenter.advance(-monthwindow,unit='month'),\
                            datecenter.advance(monthwindow,unit='month'))
    return window

def get_landsat_data(bounds, datelist, years_back=2,\
        max_cloud_thr=None, \
        bands=['B1','B2','B3','B4','B5','B7','cloud'],\
        month_aggregate=True, verbose=False): 
    '''
    Collects all landsat images from the calendar year previous of the <datelist>,
    and aggregates them into monthly means
    
    Inputs:
        bounds: <ee.bounds object> 
        datelist : <list or tuple> of date in (YY,MM,DD) format
        month_aggregate : <bool> specifies to aggregate or not 
    Output: 
        returns an Earth Engine ImageCollection object 
    '''
    #the date range for the landsat data must be a full calendar year before
    #the datelist so subtract a year from the datelist, then select
    #the window of January to December
    if max_cloud_thr is None:
        max_cloud_thr = 100
    target_year = datelist[0]
    previous_year = target_year-years_back
    l8b = ee.List(['B2','B3','B4','B5','B6','B7','BQA','cloud'])
    # rename the band list to match with the Landsat 4/5/7 bands
    l57b = ee.List(['B1','B2','B3','B4','B5','B7','BQA','cloud'])
    bands_to_select = ee.List(bands)
    l8 = ee.ImageCollection('LANDSAT/LC08/C01/T1_TOA').map(\
            ee.Algorithms.Landsat.simpleCloudScore).select(\
            l8b, l57b).filterMetadata(\
            'CLOUD_COVER', 'less_than',max_cloud_thr) #Landsat 8
    l7 = ee.ImageCollection('LANDSAT/LE07/C01/T1_TOA').map(\
            ee.Algorithms.Landsat.simpleCloudScore).select(\
            l57b).filterMetadata(\
            'CLOUD_COVER', 'less_than',max_cloud_thr) #landsat 7
    l5 = ee.ImageCollection('LANDSAT/LT05/C01/T1_TOA').map(\
            ee.Algorithms.Landsat.simpleCloudScore).select(\
            l57b).filterMetadata(\
            'CLOUD_COVER', 'less_than',max_cloud_thr) #landsat 5
    landsat = ee.ImageCollection(l5.merge(l7).merge(l8)).filter(\
            ee.Filter.calendarRange(\
            previous_year,target_year,'year')).filterBounds(bounds)
    if verbose:
        collection_size = landsat.size().getInfo()
        print(f'Found {collection_size} LANDSAT images from 01-01-{previous_year} to 12-31-{target_year}.')
        print(f'|  Month number\t|  Image count \t|')
        for month in range(1,13):
            month_landsat = landsat.filter(ee.Filter.calendarRange(month,month,'month'))
            month_landsat = month_landsat.select(bands_to_select).map(trimEdges)
            im_count = month_landsat.size().getInfo()
            print(f'|\t {month} \t|\t {im_count} \t|')
    if month_aggregate:
        landsat_monthly = []
        for month in range(1,13):
            month_landsat = landsat.filter(ee.Filter.calendarRange(month,month,'month'))
            month_bands = ee.List([f'{b}_{month}' for b in bands_to_select.getInfo()])
            month_landsat = month_landsat.select(bands_to_select,month_bands).map(trimEdges)
            monthly_mean = month_landsat.mean().float()
            landsat_monthly.append(monthly_mean)
            #data QA check, below should return 84, 
            #otherwise, not all annual LANDSAT data is available for date range
            out = ee.Image.cat(landsat_monthly)
        if verbose:
            bandcount = len(out.bandNames().getInfo())
            print(f'\nCollected LANDSAT data and aggregated to single image with {bandcount} bands represent mean month for bands: {bands}.\n')
        if  bandcount != (len(bands)*12):
            print(f'Warning!! LANDSAT data missing, only {bandcount} bands. Check date range!\n')
        return out
        '''
        ###alternative code for aggregating at the month level
        #def aggregate_monthly(m):
        #    return landsat.filter(ee.Filter.calendarRange(m,m, 'month')).select(\
        #        band_selection).map(trimEdges).mean().set('month',m)
        #months = ee.List.sequence(1,12)
        #output = months.map(aggregate_monthly)
        #return ee.ImageCollection.fromImages(output)
        '''
    else:
        return landsat.select(bands).map(trimEdges)

def get_climate_data(bounds, datelist, offset_years=29, verbose=False):
    '''
    Collects all climate images from <offset_years> previous of the <datelist>,
    and aggregates them into means and standard deviations
    
    Inputs:
        bounds: <ee.bounds object> 
        datelist : <list or tuple> of date in (YY,MM,DD) format
        offset_years : <int> years back to go from datelist[YY]
        verbose : <bool> specifies to print output
    Output: 
        returns an Earth Engine ImageCollection object 
    ''' 
    year_start = datelist[0]-offset_years
    date_start = ee.Date.fromYMD(year_start,1,1)
    date_end = ee.Date.fromYMD(datelist[0],1,1)
    date_range = ee.DateRange(date_start, date_end)
    climate_collection = ee.ImageCollection('OREGONSTATE/PRISM/AN81m').filterDate(date_range).filterBounds(bounds)
    stddev = climate_collection.reduce(ee.Reducer.stdDev())
    mean = climate_collection.reduce(ee.Reducer.mean())
    out = mean.addBands(stddev)
    if verbose:
        print(f'Collected CLIMATE data from 01-01-{year_start} to 01-01-{datelist[0]}.\n')
    return out 

def get_topographic_data(bounds, verbose=False):
    '''
    Collects all topographic images within bounds
    Inputs:
        bounds: <ee.bounds object> 
        verbose : <bool> specifies to print output
    Output: 
        returns an Earth Engine ImageCollection object 
    '''
    dem = ee.Image('USGS/NED').clip(bounds)
    slope = ee.Terrain.slope(dem)
    aspect = ee.Terrain.aspect(dem)
    out = dem.addBands(ee.Image(slope)).addBands(ee.Image(aspect))
    if verbose:
        print(f'Collected TOPOGRAPHIC data.\n')
    return out

def get_naip_data(bounds, datelist, offset_years=2,\
                bands=['R','G','B'], scale=10, verbose=False):
    '''
    Collects all naip images from <offset_years> previous of the <datelist>,
    and mosaicks them into single image
    
    Inputs:
        bounds: <ee.bounds object> 
        datelist : <list or tuple> of date in (YY,MM,DD) format
        offset_years : <int> years back to go from datelist[YY]
        bands : <list> bands to collect
        scale : <int> resolution in meters for reprojecting
        verbose : <bool> specifies to print output
    Output: 
        returns an Earth Engine ImageCollection object 
    ''' 
    start_year = datelist[0]-offset_years
    end_year = datelist[0]
    naip_collection = ee.ImageCollection('USDA/NAIP/DOQQ').filter(\
        ee.Filter.calendarRange(start_year,end_year,'year')).filterBounds(\
        bounds).select(bands)
    image_count = naip_collection.size().getInfo()
    if image_count == 0:
        datestr = str(datetime(*datelist).date()) 
        print(f'Warning, no NAIP images found within {offset_years} year(s) of {datestr}.') 
        print(f'No NAIP images collected.') 
        return []
    else:
        if verbose:
            datelist = [ee.Date(im).format('YYYY-MM-dd').getInfo() \
                 for im in naip_collection.aggregate_array('system:time_start').getInfo()]
            dtimelist = [datetime.strptime(d, '%Y-%m-%d').date() for d in datelist]
            print(f'Found {image_count} NAIP image(s) between {min(dtimelist)} and {max(dtimelist)}.\n')
            print(f'Collected NAIP and mosaicked into single image.\n')
        reproj_naip = naip_collection.mosaic().reproject(crs='EPSG:4326',scale=scale)
        return reproj_naip
 
def get_model_data(eegeom, datelist, monthwindow=1, max_cloud_thr=5, verbose=False):
    '''
    Collects all data required for RCNN model prediction <datelist>, and places in 
    single dict
    
    Inputs:
        bounds: <ee.bounds object> 
        datelist : <list or tuple> of date in (YY,MM,DD) format
        monthwindow : <int> month to go ahead/back from datelist[YY] to acquire Sentinel data
        max_cloud_thr : <int> maximum percent cloud cover to accept in Sentinel data
        verbose : <bool> specifies to print output
    Output: 
        returns a <dict>
    ''' 
 
    bounds = eegeom.bounds(proj=ee.Projection('EPSG:4326'), maxError=1)
    coords = bounds.coordinates().getInfo()[0]
    if verbose:
        print(f'Searching for Images within bounds\n')
        for c in coords:
            print(f'\t{c}')
        print(f'\n\nFor target date %02d-%02d-%02d\n'%\
            (datelist[0],datelist[1],datelist[2]))
    datewindow = create_date_range(datelist, monthwindow)
    sentinel = get_sentinel_data(bounds, datewindow, max_cloud_thr, verbose=verbose)
    landsat = get_landsat_data(bounds, datelist, max_cloud_thr, verbose=verbose)  
    climate = get_climate_data(bounds, datelist, verbose=verbose)
    topo = get_topographic_data(bounds, verbose=verbose)
    naip = get_naip_data(bounds, datelist, offset_years=1, scale=1, verbose=verbose)
    outdata = {'sentinel':sentinel, 'landsat':landsat,\
                 'climate':climate, 'topo':topo,\
                 'naip':naip}
    if verbose:
        print('Data found! Ready to send export task!\n')
        print('######################################\n')
    return outdata 


