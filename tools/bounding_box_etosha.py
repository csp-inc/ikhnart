import numpy as np
import pandas as pd


def draw_n_samples(in_min, in_max, n=100):
    return (in_max - in_min) * np.random.random_sample(n) + in_min

def main(x: list, y: list, name: str):

    lons = draw_n_samples(*x)
    lats = draw_n_samples(*y)

    df = pd.DataFrame(lats, columns=['Latitude'])
    df['Longitude'] = lons
    df['PlotKey'] = [f'pt_{str(pt).zfill(len(str(len(df["Latitude"])-1)))}' for pt in range(len(df['Latitude']))]
    df = df[['PlotKey', 'Latitude', 'Longitude']]
    df.to_csv(f'{name}_points_v1.csv', index=False)

if __name__ == '__main__':
    main(x=[15.65, 17.35], y=[-19.35, -18.35], name='etosha')
