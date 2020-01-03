import os
import json
import subprocess
import pandas as pd
if not os.path.isfile('phenocam.json'):
    subprocess.run(['wget', '-O', 'phenocam.json', 'https://phenocam.sr.unh.edu/api/cameras/?format=json&limit=10000'])
with open('phenocam.json', 'r') as fh:
    pheno = json.load(fh)
filtered_pheno = [(x["Sitename"], x["Lat"], x["Lon"]) for x in pheno["results"]]
df = pd.DataFrame(filtered_pheno, columns = ["PlotKey", "Latitude", "Longitude"])
df.to_csv('phenocam_points_v1.csv', index=False)
