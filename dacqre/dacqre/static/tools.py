import time
import ee
import numpy as np
import yaml
from . import creds

    
def pt_mapper_Wrapper(my_collection):

    def pt_mapper(feature):
        table_filt = my_collection.filterBounds(feature.geometry())
        return ee.Algorithms.If(table_filt.size().lt(ee.Number(1)),feature.set({
                'l3_key': '',
                'l4_key': ''
                }), feature.set({
                'l3_key': table_filt.first().get('l3_key'),
                'l4_key': table_filt.first().get('l4_key')
                }))
    return pt_mapper

def rename_mean_Wrapper(band_name):
    def rename_mean(feature):
        new_mean = feature.get('mean')
        return feature.set({
            band_name: new_mean
            })
    return rename_mean

def determine_zfill(in_latlons):
    zfill = 1
    for oom in [9, 99, 999, 9999, 99999]:
        if len(in_latlons) > oom:
            zfill += 1
        else:
            return zfill
    return zfill

def add_terrain_properties(image):
    elevation_band = image.select('elevation')
    slope_band  = ee.Terrain.slope(elevation_band).rename(['slope'])
    aspect_band  = ee.Terrain.aspect(elevation_band).rename(['aspect'])
    out = ee.Image.cat([elevation_band, slope_band, aspect_band])
    return out

class Static():
    def __init__(self, latlons, database, product, product_dict, **kw):
        self.latlons = latlons['points']
        self.zfill = determine_zfill(self.latlons) 
        self.name = latlons['name']
        self.database = database
        self.product = product
        print(self.product)
        self.instrument = product_dict['instrument']
        self.ee_img_id = product_dict['eeimgid']
        if 'EPA' in self.instrument:
            self.epa = True
            self.image = ee.FeatureCollection(self.ee_img_id[0])
            self.export_bands = ['l3_key', 'l4_key']
        elif (('NED' in self.instrument) or ('SRTM' in self.instrument)):
            self.epa = False
            self.image = add_terrain_properties(ee.Image(self.ee_img_id))
            self.export_bands = ['elevation', 'slope', 'aspect']
        else:
            self.epa = False
            self.image = ee.Image(self.ee_img_id)
            self.export_bands = self.image.bandNames().getInfo()
        self.selectors = ','.join(['location'] + self.export_bands)
        self.test_out = self.process_latlon()

    def process_latlon(self):
        num_points = len(self.latlons)
        plural = "s" if num_points > 1 else ""
        print('You are grabbing a static value for {} point{}. The results will be sent to the {} bucket.'.format(str(num_points), plural, self.database))
        this_ll = LatLon(self)
        this_ll.export_cloud()
        return this_ll



class LatLon():
    def __init__(self, parent):
        self.parent = parent
        self.raw_image = self.parent.image
        self.latlons = self.parent.latlons
        self.samples = self.build_fc()
        if self.parent.epa:
            self.image = self.samples.map(pt_mapper_Wrapper(self.raw_image))
        else:
            self.image = self.getpoints()
            if len(self.parent.export_bands) < 2:
                new_image = self.image.map(rename_mean_Wrapper(self.parent.export_bands[0]))
                self.image = new_image

    def getpoints(self):
        return self.raw_image.reduceRegions(
            collection=self.samples,
            reducer=ee.Reducer.mean(),
            scale=30
        )

    def build_fc(self):    
        featurelist = []
        for k, v in self.latlons.items():
            featurelist.append(ee.Feature(ee.Geometry.Point((v[1], v[0])), {'location': k}))
        return ee.FeatureCollection(featurelist)

    def export_cloud(self):
        self.description = '{}_{}'.format(self.parent.product, self.parent.name)
        self.prefix = self.description
        with open('list_of_transfers', 'a+') as fh:
            print('{}ee_export.csv'.format(self.prefix), file=fh)
        export_dict = {
                'collection': self.image,
                'description':  '{}_{}'.format(self.parent.product, self.parent.name),
                'selectors': self.parent.selectors,
                'fileNamePrefix': '{}_{}'.format(self.parent.product, self.parent.name),
                'bucket': self.parent.database
                }
        export_task = ee.batch.Export.table.toCloudStorage(**export_dict)
        export_task.start()

def pull_static(latlons, database, products, my_vars, **kw):

    my_static_list = [Static(latlons, database, product, product_dict, **kw) for product, product_dict in products.items() if product in my_vars]

    return my_static_list

def main(**in_kw):
    creds.init_creds()
    with open(in_kw["p_file"]) as products_y:
        static_raw = yaml.safe_load(products_y)
        static_base = {'products': static_raw}
    with open(in_kw["l_file"]) as ll_y:
        static_ll = yaml.safe_load(ll_y)
    static_base.update(static_ll)
    static_base['database'] = in_kw["bucket"]
    if 'all' in in_kw['my_vars']:
        static_base['my_vars'] = [k for k in static_base['products'].keys()]
    else:
        static_base['my_vars'] = in_kw["my_vars"]
    with open('cloud_files', 'r') as cloud_f:
        remote_files = cloud_f.read().splitlines()
    vars_exist = []
    for var in static_base['my_vars']:
        for fil in [fl for fl in remote_files if f'v{in_kw["version"]}' in fl]:
            if var in fil:
                print(f'{var}_{in_kw["collection"]}_v{in_kw["version"]}.csv already exists in the bucket, skipping...')
                vars_exist.append(var)
                break
    static_base['my_vars'] = [v for v in static_base['my_vars'] if v not in vars_exist]
    static_out = pull_static(**static_base)

