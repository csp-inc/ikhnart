import time
import ee
import numpy as np
import yaml
import os
from . import creds

    
def gridmet_contain_map_Wrapper(my_ic):
    def gridmet_contain_map(feature):
        amiin = feature.containedIn(my_ic.geometry())
        return feature.set('inic', amiin)
    return gridmet_contain_map

def getTS_Wrapper(my_collection, my_selectors):

    def getTS(image):
        my_reducer = ee.Reducer.mean()
        if len(my_selectors) < 2:
            my_reducer = my_reducer.setOutputs(my_selectors)
        collection_with_ts = image.reduceRegions(
            collection=my_collection,
            reducer=my_reducer,
            scale=30
        )
        def setDate(feature):
            return feature.set('img_date', ee.Date(image.get('system:time_start')).format('Y-MM-dd'))
        return collection_with_ts.map(setDate)
    return getTS

def addRow(image):
    row = ee.Image.constant(image.get('WRS_ROW')).rename(['row'])
    return image.addBands(row)

def addPath(image):
    path = ee.Image.constant(image.get('WRS_PATH')).rename(['path'])
    return image.addBands(path)

def add_sensor_info_Wrapper(my_sensor):
    def add_sensor_info(image):
        this_sensor = ee.Image(my_sensor).rename(['sensor'])
        return image.addBands(this_sensor)
    return add_sensor_info

def addNDVI_Wrapper(nir_band, red_band):
    def addNDVI(image):
        ndvi = image.normalizedDifference([nir_band, red_band]).rename(['NDVI'])
        return image.addBands(ndvi)
    return addNDVI

def remove_low_reds(image):
    red_mask = image.select('RED').gte(0)
    return image.updateMask(red_mask)

def add_band_properties(image):
    if image.bandNames().size().lte(11):
        nir_band  = image.select('B4').rename(['NIR'])
        red_band  = image.select('B3').rename(['RED'])
        blue_band = image.select('B1').rename(['BLUE'])
    else:
        nir_band  = image.select('B5').rename(['NIR'])
        red_band  = image.select('B4').rename(['RED'])
        blue_band = image.select('B2').rename(['BLUE'])
    return image.addBands(nir_band).addBands(red_band).addBands(blue_band)

def rename_MODIS(image):
    return image.select(['NDVI', 'EVI', 'SummaryQA', 'DayOfYear']).rename(['NDVI_int', 'EVI_int', 'SummaryQA', 'DayOfYear'])

def normalize_MODIS(image):
    ndvi = image.expression(
        'NDVI_int * 0.0001', {
          'NDVI_int': image.select('NDVI_int'),
    }).rename(['NDVI'])
    evi = image.expression(
        'EVI_int * 0.0001', {
          'EVI_int': image.select('EVI_int'),
    }).rename(['EVI'])
    return image.addBands(evi).addBands(ndvi)

def addEVI_Wrapper(nir_band, red_band, blue_band):
    def addEVI(image):
        evi = image.expression(
            '2.5 * (((NIR - RED) * 0.0001) / ((NIR * 0.0001) + 6 * (RED * 0.0001) - 7.5 * (BLUE * 0.0001) + 1))', {
              'NIR': image.select(nir_band),
              'RED': image.select(red_band),
              'BLUE': image.select(blue_band)
        }).rename(['EVI'])
        return image.addBands(evi)
    return addEVI

def add_num_bands(image):
    num_bands = image.bandNames().size()
    return image.set('num_bands', num_bands)

def jan_1_str(in_yr):
    return '{}-01-01'.format(str(in_yr))

def determine_zfill(in_latlons):
    zfill = 1
    for oom in [9, 99, 999, 9999, 99999]:
        if len(in_latlons) > oom:
            zfill += 1
        else:
            return zfill
    return zfill

class TimeSeries():
    def __init__(self, latlons, database, product, product_dict, **kw):
        print(f'Building {product} time series.')
        self.all_pr = []
        self.latlons = latlons['points']
        self.zfill = determine_zfill(self.latlons) 
        self.name = latlons['name']
        if 'pathrows' in latlons.keys():
            self.prs = latlons['pathrows']
        else:
            self.prs = None
        if 'repeat' in kw['end_date'] or not kw['end_date']:
            self.end_date       = ee.Date('3000-01-01')
        else:
            self.end_date       = ee.Date(kw['end_date'])
        self.database       = database
        self.product        = product
        self.instrument     = product_dict['instrument']
        self.ee_img_ids     = product_dict['eeimgid']
        self.selector_list  = product_dict['selector_list']
        self.sensors        = product_dict['sensors']
        if product_dict['last_date']:
            self.start_date     = ee.Date(product_dict['last_date']).advance(1, 'day')
        else:
            self.start_date     = ee.Date('1970-01-01')
        self.date_range = self.end_date.difference(self.start_date, 'day').getInfo()
        if self.date_range < 0:
            self.start_date     = ee.Date('1970-01-01')
            self.date_range = self.end_date.difference(self.start_date, 'day').getInfo()

        #if self.instrument == 'GDDP':
            # need to build in here a variable for model and scenario
            # possible solution is using a initial_projection_parameters.yaml
            # for now only hard code the model and scenario
        #    self.model     = 'CESM-BGC' #kw['model']
        #    self.scenario  = 'rcp85' #kw['scenario']
        #    self.image_collections = [ee.ImageCollection(img_id).filter(ee.Filter.date(self.start_date, self.end_date.advance(1, 'day'))).filter(ee.Filter.eq('model', self.model)).filter(ee.Filter.eq('scenario',self.scenario)) for img_id in self.ee_img_ids]
        #else:

        self.image_collections = [ee.ImageCollection(img_id).filter(ee.Filter.date(self.start_date, self.end_date.advance(1, 'day'))) for img_id in self.ee_img_ids]
        self.test_out = self.process_latlon()

    def process_latlon(self):
        if 'LANDSAT' in self.instrument:
            num_batches = len(self.prs.keys())
            for my_batch, (pr, prlist) in enumerate(self.prs.items()):
                num_points = len(prlist)
                plural = "s" if num_points > 1 else ""
                print('You are grabbing a time-series for {} point{}. This is batch {} of {}. The results will be sent to the {} bucket.'.format(str(num_points), plural, str(my_batch+1), num_batches, self.database))
                this_ll = LatLon(self, pr, prlist)
                this_ll.export_cloud()
                self.all_pr.append(this_ll)
            return self.all_pr
        elif ('GRIDMET' in self.instrument): #or 'GDDP' in self.instrument): 
            num_points = len(self.latlons)
            plural = "s" if num_points > 1 else ""
            self.start_year = int(self.start_date.get('year').getInfo())
            self.all_image_collections = self.image_collections
            self.collection_end_dates = [ee.List(imgcol.get('date_range')).get(1) for imgcol in self.all_image_collections]
            date_max = max(self.collection_end_dates)
            self.last_year = ee.Date(date_max).get('year').getInfo()
            all_yr = []
            for yr in np.arange(self.start_year, self.last_year+1):
                print(jan_1_str(yr), jan_1_str(yr+1))
                self.image_collections = [my_ic.filter(ee.Filter.date(jan_1_str(yr), jan_1_str(yr+1))) for my_ic in self.all_image_collections]
                print('You are grabbing a time-series for {} point{} for year {}. The results will be sent to the {} bucket.'.format(str(num_points), plural, str(yr), self.database))
                this_ll = LatLon(self, str(yr))
                this_ll.export_cloud()
                all_yr.append(this_ll)
            return all_yr

        else:
            num_points = len(self.latlons)
            plural = "s" if num_points > 1 else ""
            print('You are grabbing a time-series for {} point{}. The results will be sent to the {} bucket.'.format(str(num_points), plural, self.database))
            this_ll = LatLon(self, 'all')
            this_ll.export_cloud()
            return this_ll

class LatLon():
    def __init__(self, parent, my_pr, prlist=[]):
        self.parent = parent
        self.name = my_pr
        self.prlist = prlist
        self.selector_list = self.parent.selector_list
        self.selectors = 'img_date,location'
        self.latlons = self.parent.latlons
        if 'LANDSAT' in self.parent.instrument:
            self.latlons = {k: self.parent.latlons[k] for k in self.prlist}
            self.path, self.row = tuple([int(x) for x in self.name.split('_')[1::2]])
            self.nirs = ['B4', 'B4', 'B4', 'B5']
            self.reds = ['B3', 'B3', 'B3', 'B4']
            self.blues = ['B1', 'B1', 'B1', 'B2']
            self.filtered_ics = self.filter_pr()
            self.image_collections = self.get_landsat_ndvi_and_evi()
        elif 'NBR' in self.parent.instrument:
            self.image_collections = self.filter_ic()
        elif 'MTBS' in self.parent.instrument:
            self.filtered_ics = self.filter_ic()
            self.image_collections = self.get_mtbs()
        elif 'MODIS' in self.parent.instrument:
            self.filtered_ics = self.filter_ic()
            self.image_collections = self.modis_qa()
        else:
            self.image_collections = self.parent.image_collections
        self.selectors = ','.join(self.selector_list) + ',' + self.selectors
        self.total_imgs = np.sum([ic.size().getInfo() for ic in self.image_collections])
        if self.total_imgs < 1:
            if self.parent.date_range < 0:
                print('The start date for this retrieval is based upon the files that currently exist in the bucket.')
                print('The file in the bucket has produced a start date that is after the end date specified.')
                print('Therefore, no images will be retrieved.')
            else:
                print('No images available in date range')
            with open(os.path.join('logs', 'images_not_available'), 'a+') as fh:
                print(self.parent.product, file=fh)
        else:
            self.samples = self.build_fc()
            if ('GRIDMET' in self.parent.instrument): #or 'GDDP' in self.parent.instrument): 
                self.samples = self.gridmet_spatial_filter()
            self.fcs = [ic.map(getTS_Wrapper(self.samples, self.selector_list)) for ic in self.image_collections]
            self.flat_cs = [this_fc.flatten() for this_fc in self.fcs]
            if len(self.flat_cs) > 1:
                my_fc = self.flat_cs[0]
                for fc in self.flat_cs[1:]:
                    my_fc = my_fc.merge(fc)
                self.flat_collection = my_fc
            else:
                self.flat_collection = self.flat_cs[0]

    def filter_pr(self):
        return [raw_ic.filter(ee.Filter.And(ee.Filter.eq('WRS_PATH', self.path), ee.Filter.eq('WRS_ROW', self.row))) for raw_ic in self.parent.image_collections]

    def filter_ic(self):
        lat, lon = list(zip(*self.latlons.values()))
        boundingbox = ee.Geometry.Rectangle(np.min(lon) - 0.1, np.min(lat) - 0.1, np.max(lon) + 0.1, np.max(lat) + 0.1)
        my_filtered_ic = [raw_ic.filterBounds(boundingbox) for raw_ic in self.parent.image_collections]
        return my_filtered_ic

    def get_mtbs(self):
        return [filt_ic.map(add_num_bands).filter(ee.Filter.gt('num_bands', 1)) for filt_ic in self.filtered_ics]

    def modis_qa(self):
        renamed_ics = [filt_ic.map(rename_MODIS) for filt_ic in self.filtered_ics]
        return [renamed_ic.map(normalize_MODIS) for renamed_ic in renamed_ics]

    def gridmet_spatial_filter(self):
        tight_geo = self.samples.map(gridmet_contain_map_Wrapper(self.image_collections[0]))
        return tight_geo.filter(ee.Filter.eq('inic', True))

    def get_gridmet(self):
        return [filt_ic.select(
            ['tmmn', 'tmmx', 'vpd']
            ) for filt_ic in self.parent.image_collections]

    def get_landsat_ndvi_and_evi(self):
        ndvi_evi_with_prs = [filt_ic.map(
            add_sensor_info_Wrapper(sensor)
            ).map(
            addNDVI_Wrapper(nir, red)
            ).map(
            addEVI_Wrapper(nir, red, blue)
            ).map(
            addPath
            ).map(
            addRow
            ) for filt_ic, nir, red, blue, sensor in zip(self.filtered_ics, self.nirs, self.reds, self.blues, self.parent.sensors)]
        return [item.select(self.selector_list) for item in ndvi_evi_with_prs]

    def build_fc(self):    
        featurelist = []
        for k, v in self.latlons.items():
            featurelist.append(ee.Feature(ee.Geometry.Point((v[1], v[0])), {'location': k}))
        return ee.FeatureCollection(featurelist)

    def export_cloud(self):
        if self.total_imgs > 0:
            self.description = '{}_{}_{}'.format(self.parent.product, self.parent.name, self.name)
            self.prefix = self.description
            with open('list_of_transfers', 'a+') as fh:
                print('{}ee_export.csv'.format(self.prefix), file=fh)
            export_task = ee.batch.Export.table.toCloudStorage(
                collection=self.flat_collection,
                description = self.description,
                fileNamePrefix = self.prefix,
                selectors=self.selectors,
                bucket=self.parent.database
            )
            export_task.start()
            if self.prlist:
                time.sleep(3)

def pull_ts(latlons, database, products, my_vars, **kw):

    my_ts_list = [TimeSeries(latlons, database, product, product_dict, **kw) for product, product_dict in products.items() if product in my_vars]

    return my_ts_list

def main(**in_kw):
    creds.init_creds()
    with open(in_kw["p_file"]) as products_y:
        ts_raw = yaml.safe_load(products_y)
        for k in ts_raw.keys():
            ts_raw[k]['last_date'] = ''
            if not in_kw['diff_run']:
                for dk, dv in in_kw['dates_dict'].items():
                    if k == dk:
                        ts_raw[k]['last_date'] = dv
        ts_base = {'products': ts_raw}
    with open(in_kw["l_file"]) as ll_y:
        ts_ll = yaml.safe_load(ll_y)
    ts_base.update(ts_ll)
    ts_base['end_date'] = in_kw["end_date"]
    if ts_base['end_date']:
        try:
            ee.Date(ts_base['end_date']).getInfo()
        except:
            print('You have attempted to provided an end_date that is not convertible to an Earth Engine date.')
            print(f'It is possible that the date provided, {ts_base["end_date"]}, is not formatted correctly.')
            print('The correct format is of the form "YYYY-MM-DD".')
            print('Please try again.')
            return
        else:
            pass
    ts_base['database'] = in_kw["bucket"]
    if 'all' in in_kw['my_vars']:
        ts_base['my_vars'] = list(ts_base['products'].keys())
    else:
        ts_base['my_vars'] = in_kw["my_vars"]
    #the all does not work with GDDP, we will remove this option in the tests.
    #if 'GDDP' in in_kw['my_vars']:
    #    ts_base['model'] = in_kw["model"]
    #    ts_base['scenario'] = in_kw["scenario"]
    ts_out = pull_ts(**ts_base)
    print('Tasks sent, pending downloads to bucket')
