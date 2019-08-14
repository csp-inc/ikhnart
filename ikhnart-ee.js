//var ikhnart = Table('users/tony-csp/ikhnart_bounds')

var tools = require('users/tony-csp/default:tools')

var ikhnart_bb = ee.FeatureCollection([
  ee.Feature(
    ee.Geometry.Rectangle(108.5471, 45.33891, 108.8689, 45.86695),
    {name: 'Ikh Nart'})]);
    
// initial variables
var geometry = ikhnart;
var clipper = function(img)
  {return img.clip(geometry)};
  
var addTime = function(image) {
  return image.addBands(image.metadata('system:time_start')
    .divide(1000 * 60 * 60 * 24 * 365));
};

var fill = function(image){
                var filled1a = image.focal_mean(2, 'square', 'pixels', 1).blend(image);
                return filled1a.set('system:time_start',image.get('system:time_start'));
};

// Define a FeatureCollection: Ikh Nart and Do
var bands = ['B5', 'B4', 'B3', 'B2', 'B1'];
var L5coll = ee.ImageCollection('LANDSAT/LT05/C01/T1_SR')
.filter(ee.Filter.lt('CLOUD_COVER',25))
.select(bands)
.filterBounds(geometry)


var L7coll = ee.ImageCollection('LANDSAT/LE07/C01/T1_SR')
.filter(ee.Filter.lt('CLOUD_COVER',25))
.select(bands)
.filterBounds(geometry)
.map(fill)

var L8coll = ee.ImageCollection('LANDSAT/LC08/C01/T1_SR')
.filter(ee.Filter.lt('CLOUD_COVER',5))
.filterBounds(geometry)
.map(function(image){
  return image.rename(['B0', 'B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B9', 'B10', 'B11']);
})
.select(bands);

var addNDVI = function(image) {
  var ndvi = image.normalizedDifference(['B4', 'B3']).rename('NDVI');
  return image.addBands(ndvi);
};

var landsat = ee.ImageCollection(L5coll.merge(L7coll.merge(L8coll)))
.map(addNDVI)
.map(clipper);

var months = ee.List.sequence(1, 12);

// Group by month, and then reduce within groups by mean();
// the result is an ImageCollection with one image for each
// month.
var byMonth = ee.ImageCollection.fromImages(
      months.map(function (m) {
        return landsat.filter(ee.Filter.calendarRange(m, m, 'month'))
                    .select('NDVI').median()
                    .set('month', m);
}));
print(byMonth);

var ndviParams = {min: -0.5, max: 1, palette: 
["#440154FF", "#482173FF", "#433E85FF", "#38598CFF", "#2D708EFF", "#25858EFF", "#1E9B8AFF",
 "#2BB07FFF", "#51C56AFF", "#85D54AFF", "#C2DF23FF", "#FDE725FF"]};

//var display = function(image){
//  return Map.addLayer(ee.Image(image),ndviParams);
//};

//byMonth.map(display);

//Map.addLayer(ee.Image(byMonth.first()), ndviParams, 'monthly NDVI');

tools.map.addImageCollection(byMonth, {
  vis: ndviParams,
  label: 'month'
})

var years = ee.List.sequence(1984, 2019);

/*
var collectYear = ee.ImageCollection(years
.map(function(y) {
    var start = ee.Date.fromYMD(y, 1, 1)
    var end = start.advance(12, 'month');
    return collection_merge.filterDate(start, end).reduce(ee.Reducer.median())
}));

var nullimages = collectYear
    .map(function(image) {
      return image.set('count', image.bandNames().length())
    })
    .filter(ee.Filter.eq('count', 1));
print(nullimages);
*/
/*
var medianFirst = collection_merge.first()
var finalCollection = nullimages.map(function(image){
  return image.visualize({bands: ['B3_median', 'B2_median', 'B1_median'], min: 300, max: 1800});
})
Map.addLayer(medianFirst, {bands: ['B3', 'B2', 'B1'], min: 0, max: 3000}, 'first image');
*/
/*
Export.video.toDrive({
  collection: finalCollection,
  description: 'yearly-ikhnart',
  dimensions: 1080,
  framesPerSecond: 1,
  region: geometry
});
*/
/*
var dem = ee.Image('USGS/SRTMGL1_003').clip(geometry);
var elevation = dem.select('elevation');
var slope = ee.Terrain.slope(elevation);

//Map.addLayer(features, {}, 'Ikh Nart')
Map.setCenter(108.7, 45.6, 9); // Ikh Nart
Map.addLayer(elevation, {min: 0, max:3500}, 'elevation')
Map.addLayer(slope, {min: 0, max: 60}, 'slope');

// This function adds a band representing the image timestamp.
*/
var climate = ee.ImageCollection('IDAHO_EPSCOR/TERRACLIMATE')
                  .filter(ee.Filter.date('1970-01-01', '2019-08-01'))
                  .map(clipper)
                  .map(addTime);

var climateByMonth = ee.ImageCollection.fromImages(
      months.map(function (m) {
        return climate.filter(ee.Filter.calendarRange(m, m, 'month'))
                    .reduce(ee.Reducer.median())
                    .set('month', m);
}));

print(climateByMonth);

//var climateMedians = climate.reduce(ee.Reducer.median());
/*
var tmmx = climateMedians.select('tmmx_median');
var tmmxVis = {
  min: 0.0,
  max: 130.0,
  palette: [
    '1a3678', '2955bc', '5699ff', '8dbae9', 'acd1ff', 'caebff', 'e5f9ff',
    'fdffb4', 'ffe6a2', 'ffc969', 'ffa12d', 'ff7c1f', 'ca531a', 'ff0000',
    'ab0000'
  ],
};

Map.addLayer(tmmx, tmmxVis,'Maximum Temperature');

// Load a MODIS collection, filter to several years of 16 day mosaics,
// and map the time band function over it.
var collection = ee.ImageCollection('MODIS/006/MYD13A1')
  .filterDate('2000-01-01', '2019-08-01')
  .map(clipper)
  .map(addTime);

// Select the bands to model with the independent variable first.
var trend = collection.select(['system:time_start', 'NDVI'])
  // Compute the linear trend over time.
  .reduce(ee.Reducer.linearFit());

// Display the trend with increasing slopes in green, decreasing in red.
Map.addLayer(
    trend,
    {min: 0, max: [-100, 100, 10000], bands: ['scale', 'scale', 'offset']},
    'NDVI trend');
// Select the bands to model with the independent variable first.
*/
/*
var trend = climate.select(['system:time_start', 'tmmx'])
  // Compute the linear trend over time.
  .reduce(ee.Reducer.linearFit());
*/

var batch = require('users/fitoprincipe/geetools:batch')
batch.Download.ImageCollection
.toDrive(climateByMonth, "users/tony-csp", {scale:30, region: geometry});
/*
Export.image.toCloudStorage({
  image: byMonth,
  description: 'monthly-ndvi',
  bucket: 'ikhnart',
  fileNamePrefix: 'geotiff/ndvi',
  scale: 30,
  region: geometry
});


Export.image.toCloudStorage({
  image: elevation,
  description: 'srtm-slope',
 bucket: 'ikhnart',
  fileNamePrefix: 'geotiff/srtm-slope',
  scale: 30,
  region: features
});
*/
