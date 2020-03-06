import geopandas as gpd
import os
import numpy as np
from shapely.geometry import Polygon, MultiPolygon

def reproject_shp(filename, outname=None, crs={'init':'epsg:4326'}):
    '''
    Opens a shape file and reprojects to EPSG:4326 
    and saves in GeoJSON format
    =============================================
    Input:
        filename <str>
    Output:
        None
    '''
    name = filename.split('.')[1]
    shp = gpd.read_file(filename)
    if not os.path.isdir('data/json'):
        os.mkdir('data/json') 
    if not outname:
        outname = f'data/json/{name}.geojson'
    shp.to_crs(crs).to_file(outname, driver='GeoJSON')
    print(f'Wrote {outname}! in projection: {crs}')
    return 0

def simplify_geometry(df, tol=0.05):
    s = df.copy()
    simple_geom = [feature.simplify(tol) for feature in df.geometry]
    s.geometry=simple_geom
    return s

def cull_multipolygon(multipolygon, minimum_size=1):
    features = [f for f in multipolygon if f.area >= minimum_size]
    if len(features) > 1:
        return MultiPolygon(features)
    return features[0]

def cull_geometry(df, minimum_size=1):
    s = df.copy()
    culled_polygons = [feature if feature.geom_type == 'Polygon' \
                        else cull_multipolygon(feature, minimum_size) for feature in s.geometry]
    s.geometry = culled_polygons
    return s 

def getXYCoords(geometry, coord_type):
    """ Returns either x or y coordinates from  geometry coordinate sequence. Used with LineString and Polygon geometries."""
    if coord_type == 'x':
        return geometry.coords.xy[0]
    elif coord_type == 'y':
        return geometry.coords.xy[1]

def getPolyCoords(geometry, coord_type):
    """ Returns Coordinates of Polygon using the Exterior of the Polygon."""
    ext = geometry.exterior
    return getXYCoords(ext, coord_type)

def getLineCoords(geometry, coord_type):
    """ Returns Coordinates of Linestring object."""
    return getXYCoords(geometry, coord_type)

def getPointCoords(geometry, coord_type):
    """ Returns Coordinates of Point object."""
    if coord_type == 'x':
        return geometry.x
    elif coord_type == 'y':
        return geometry.y

def multiGeomHandler(multi_geometry, coord_type, geom_type):
    """
    Function for handling multi-geometries. Can be MultiPoint, MultiLineString or MultiPolygon.
    Returns a list of coordinates where all parts of Multi-geometries are merged into a single list.
    Individual geometries are separated with np.nan which is how Bokeh wants them.
    # Bokeh documentation regarding the Multi-geometry issues can be found here (it is an open issue)
    # https://github.com/bokeh/bokeh/issues/2321
    """

    for i, part in enumerate(multi_geometry):
        # On the first part of the Multi-geometry initialize the coord_array (np.array)
        if i == 0:
            if geom_type == "MultiPoint":
                coord_arrays = np.append(getPointCoords(part, coord_type), np.nan)
            elif geom_type == "MultiLineString":
                coord_arrays = np.append(getLineCoords(part, coord_type), np.nan)
            elif geom_type == "MultiPolygon":
                coord_arrays = np.append(getPolyCoords(part, coord_type), np.nan)
        else:
            if geom_type == "MultiPoint":
                coord_arrays = np.concatenate([coord_arrays, np.append(getPointCoords(part, coord_type), np.nan)])
            elif geom_type == "MultiLineString":
                coord_arrays = np.concatenate([coord_arrays, np.append(getLineCoords(part, coord_type), np.nan)])
            elif geom_type == "MultiPolygon":
                coord_arrays = np.concatenate([coord_arrays, np.append(getPolyCoords(part, coord_type), np.nan)])

    # Return the coordinates
    return coord_arrays


def getCoords(row, geom_col, coord_type):
    """
    Returns coordinates ('x' or 'y') of a geometry (Point, LineString or Polygon) as a list (if geometry is LineString or Polygon).
    Can handle also MultiGeometries.
    """
    # Get geometry
    geom = row[geom_col]

    # Check the geometry type
    gtype = geom.geom_type

    # "Normal" geometries
    # -------------------

    if gtype == "Point":
        return getPointCoords(geom, coord_type)
    elif gtype == "LineString":
        return list( getLineCoords(geom, coord_type) )
    elif gtype == "Polygon":
        return list( getPolyCoords(geom, coord_type) )

    # Multi geometries
    # ----------------

    else:
        return list( multiGeomHandler(geom, coord_type, gtype) )
