make_dacqre <- function(collection, data, lon_col, lat_col, id_col, 
                        project = 'csp-projects',
                        bucket = 'testing-123',
                        assets = c('Landsat', 'Daymet')
                        ) {
  
  # collection: name of collection
  # data:     in-memory data frame
  # lon_col:  longitude column 
  # lat_col:  latitude column 
  # id_col:   column containing a unique sample id for each record

  new_data <- data[c(id_col, lat_col, lon_col)]
  colnames(new_data) <- c('PlotKey', 'Latitude', 'Longitude')
  write.csv(new_data, paste0(collection, '_points_v1.csv'))

#  cmd <- paste('./dacqre-serve.py', 
#        '--csv', temp_csv,
#        '--project', project,
#        '--bucket', bucket,
#        '--assets', paste(assets, collapse = ' '))
#  system(cmd)
  
}

# Example call
trails_sample <- read.csv('trails-sample.csv')
make_dacqre(trails_sample, lon_col = 'X', lat_col = 'Y', id_col = 'ID')
