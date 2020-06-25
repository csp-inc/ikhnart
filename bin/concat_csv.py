import dask.dataframe as dd
from glob import glob
import pandas as pd
import numpy as np

rcp = ['rcp45', 'rcp85']
wd = './riomora/data'
destination = '/datadrive/riomora'
collection = 'wdpa-555609346'
dataset = 'GDDP'
version = 'v1'

for r in rcp:
    df = pd.concat([pd.read_csv(f) for f in glob(f'{wd}/*{r}*')])
    #df = dd.read_csv(f'{wd}/*{r}*') #dask method, but saves as a directory...
    df.to_csv(f'{destination}/{dataset}_{r}_{collection}_{version}.csv', index=False)
    
