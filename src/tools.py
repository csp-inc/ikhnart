# tools for GCM data processing
import pandas as pd
import numpy as np
import dask.dataframe as dd

def ag_func(df):
    d = {}
    d['tasmax'] = df['tasmax'].mean()
    d['tasmin'] = df['tasmin'].mean()
    d['pr'] = df['pr'].sum()
    return pd.Series(d)

def aggregate_by_model(df, model_name, year_range=(2006,2100)):
    query = df.xs(model_name, level='model')
    query = query[(query.index.year >= year_range[0]) & (query.index.year <= year_range[1])]
    q_agg = query.groupby([query.index.year, \
    query.index.month]).apply(ag_func)
    q_agg.index.names = ['year', 'month']
    columns = [(f'{model_name}',n) for n in q_agg.columns.values]
    q_agg.columns = pd.MultiIndex.from_tuples(columns)
    return q_agg

def create_gcm_summary(filename, year_range=(2006,2100)):
    #df = pd.read_csv(glob(f'{wd}/*{s}*')[0], chunksize=1e5)
    df = dd.read_csv(filename)
    df['img_date'] = df['img_date'].astype('datetime64')
    df['tasmin'] = (df['tasmin'] - 273.15)/10
    df['tasmax'] = (df['tasmax']- 273.15)/10
    df['pr'] = df['pr'] * 86400
    groups = df.groupby(['img_date','model'])['tasmax','tasmin','pr'].mean().compute()
    model_list = np.unique(np.array([v[1] for v in groups.index.values]))
    df_summary = pd.concat([aggregate_by_model(groups, model, year_range=year_range)\
            for model in model_list],\
    axis=1).dropna()
    df_summary.columns.names = ['model', 'climate']
    return df_summary
