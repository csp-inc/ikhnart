from glob import glob
import pandas as pd
import os
import sys

def change_header(df):
    mapping = {'Latitude':['LAT','Lat','lat','latitude','Latitude','y','Y'],\
                'Longitude':['LON','Lon','lon','long','longitude','Longitude','x','X'],\
                'PlotKey':['plotkey','loc','loc_id','id','ID','Key','Plot','CN']}
    column_map = {}
    for c in df.columns:
        for m in mapping:
            if c in mapping[m]:
                column_map.update({c:m})
    return(df.rename(columns=column_map))

if __name__ == '__main__':

    wd = '/datadrive'
    sample_dirc = f'{wd}/random-samples'
    filelist = sorted(glob(f'{sample_dirc}/*.csv'))

    for f in filelist:
        collection_name = os.path.basename(f).split('.')[0].lower()
        temp = change_header(pd.read_csv(f))
        outdirc = 'collections'
        if not os.path.exists(outdirc):
            os.mkdir(outdirc)
        if os.path.exists(f'{outdirc}/sample_points_v1.csv'):
            os.remove(f'{outdirc}/sample_points_v1.csv') #delete sample file
        outname = f'{outdirc}/{collection_name}_points_v1.csv'
        print(f'writing {outname}')
        temp.to_csv(outname, index=False)
