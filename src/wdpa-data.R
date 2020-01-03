#!/usr/bin/env Rscript

args = commandArgs(trailingOnly=TRUE)

library(tidyverse)
library(sf)
library(mapview)
library(digest)
library(lubridate)


# ---- settings ---------------------------------------------------------------

seed <- 123

n_prot_areas_targeted <- ifelse(  # the number of protected areas to draw
  length(args) == 0, 1, as.integer(args[1]))  

n_locs_targeted <- ifelse(  # the number of locations to sample per protected area
  length(args) %in% c(0, 1), 100, as.integer(args[2]))   

sample_cellsize <- 1000
 
message(
  sprintf("Using `n_prot_areas_targeted` = %s and `n_locs_targeted` = %s.",
          n_prot_areas_targeted, n_locs_targeted)
)

# ---- data -------------------------------------------------------------------

# Create the directory tree needed to store the assets developed below.
invisible({
  sapply(c("plots", "random-samples"), function(x) {
    dir.create(file.path("/data/thin-section", x),
               showWarnings = FALSE, recursive = TRUE)
  })
})

# Load the tabular and spatial protected areas data.
if (!exists('wdpa_shp')) {  # a failsafe control-flow because this is slow
  wdpa_shp_file <- list.files("/data", pattern = ".*shapefile-polygons.shp$",
                              full.names = TRUE, recursive = TRUE)
  wdpa_release <- str_extract(wdpa_shp_file,
                              paste(paste0(month.abb[1:12], '*\\d{4}'), collapse = "|"))
  latest_release_idx <- which.max(parse_date_time(wdpa_release, "b!Y!"))
  sql_query <- sprintf(
    "SELECT * FROM \"%s\" WHERE MARINE = '0' AND IUCN_CAT IN ('Ia', 'Ib', 'II')",
    st_layers(wdpa_shp_file[latest_release_idx])$name
  )
  wdpa_shp <- st_read(wdpa_shp_file[latest_release_idx],
                      query = sql_query,
                      int64_as_string = FALSE)
}

area_release_attr <- sprintf("area_sq_m_%s", wdpa_release[latest_release_idx])
wdpa_shp_areas <- as_tibble(st_drop_geometry(wdpa_shp)) %>%
  mutate(!!area_release_attr := as.double(st_area(wdpa_shp)))

write_csv(wdpa_shp_areas %>% select(WDPAID, WDPA_PID, !!area_release_attr),
          file.path("/data", sprintf("wdpa-polygons-areas-%s.csv",
                                     wdpa_release[latest_release_idx])))


# ---- filtering / selection --------------------------------------------------

wdpa_summary <- wdpa_shp_areas %>%
  rename(area_sq_m = !!area_release_attr) %>%
  group_by(WDPAID) %>%
  summarise(area_sq_m = sum(area_sq_m)) %>%
  ungroup() %>%
  mutate(rel_area = area_sq_m / sum(area_sq_m),
         int_hash = digest2int(as.character(WDPAID), seed = seed),
         selector = rel_area / abs(int_hash)) %>%
  arrange(desc(selector)) %>%
  slice(1:n_prot_areas_targeted)
write_csv(wdpa_summary, file.path("/data/thin-section",
                                  sprintf("wdpa-selection-summary-%s.csv",
                                          wdpa_release[latest_release_idx])))


wdpa_shp_thin <- wdpa_shp %>%
  filter(WDPAID %in% wdpa_summary$WDPAID) %>%  # dim(wdpa_shp_thin)
  left_join(select(wdpa_summary, WDPAID, selector)) %>%
  arrange(desc(selector))
st_write(wdpa_shp_thin,
         file.path("/data/thin-section",
                   sprintf("wdpa-selected-polygons-%s.geojson",
                           wdpa_release[latest_release_idx])),
         delete_dsn = TRUE)
rm(list = c("wdpa_shp")); gc()

# polygons_areas_breadcrumbs <-
#   list.files("/data", pattern = ".*polygons-areas.*.csv",
#              full.names = TRUE, recursive = TRUE)
# polygons_areas <- lapply(polygons_areas_breadcrumbs, read_csv,
#                          col_types = cols("i", "c", "d")) %>%
#   reduce(full_join)
# grep("area", names(polygons_areas), value = TRUE)

# which(wdpa_shp_thin$WDPAID == 650)
cache_dir <- "/data/thin-section/random-samples"

sample_lat_lon_list <- lapply(wdpa_shp_thin$WDPAID, function(x) {  # 4367

  message(sprintf("Developing samples for WPAID %s...", x))

  this_pa_info <- filter(wdpa_summary, WDPAID == x)
  pa_key <- this_pa_info$WDPAID

  this_pa_shp <- filter(wdpa_shp_thin, WDPAID == x)

  bb <- st_bbox(this_pa_shp)
  bb_coords <- st_coordinates(st_as_sfc(bb)) %>%
    as_tibble() %>%
    st_as_sf(coords = c("X", "Y"), crs = 4326)

  x_dist <- st_distance(bb_coords[1, ], bb_coords[2, ])[1, 1]
  n_x <- as.integer(ceiling(x_dist / (sample_cellsize)))

  y_dist <- st_distance(bb_coords[2, ], bb_coords[3, ])[1, 1]
  n_y <- as.integer(ceiling(y_dist / (sample_cellsize)))

  loc_grid_raw <- st_make_grid(this_pa_shp, n = c(n_x, n_y),
                          square = TRUE, what = "centers")
  which_in_bounds <- st_intersects(st_transform(this_pa_shp, 3857),
                                 st_transform(loc_grid_raw, 3857))
  loc_grid <- loc_grid_raw[unlist(which_in_bounds)]

  # mapview(this_pa_shp) + mapview(loc_grid)
  # (n_x * n_y) == length(test)
  # as.double(st_area(loc_grid[1])) / (sample_cellsize)^2

  set.seed(seed)
  keepers <- sample(1:length(loc_grid),
                    size = min(n_locs_targeted, length(loc_grid)))

  m <- mapview(this_pa_shp, legend = FALSE, col.regions = '#377eb8',
               layer.name = paste(unique(this_pa_shp$NAME), collapse = " and ")) +
    mapview(loc_grid[keepers], legend = FALSE, col.regions = '#e41a1c',
            homebutton = FALSE)
  mapshot(m, url = file.path(cache_dir,
                             sprintf("WDPA-%s-map.html", pa_key)))

  sample_lat_lon <- st_transform(loc_grid[keepers], 4326) %>%
    st_coordinates() %>%
    as_tibble() %>%
    rename(Longitude = X, Latitude = Y) %>%
    mutate(loc_id = paste(this_pa_info$WDPAID, 1:n(), sep = "_"))

  write_csv(sample_lat_lon,
            file.path(cache_dir, sprintf("WDPA-%s.csv", pa_key)))


  this_pa_shp_bbox <-
    st_as_sfc(st_bbox(st_combine(this_pa_shp)))
  st_write(this_pa_shp_bbox,
           file.path(cache_dir, sprintf("WDPA-%s-bbox.geojson", pa_key)),
           delete_dsn = TRUE)

  rm(list = c("this_pa_shp", "loc_grid_raw", "loc_grid", "keepers", "m")); gc()
  sample_lat_lon

})

# ls /data/thin-section/random-samples/*.csv | wc -l

m <- mapview(st_centroid(st_transform(wdpa_shp_thin, 3857)),
             legend = FALSE, col.regions = '#4daf4a',
             homebutton = FALSE) +
  mapview(wdpa_shp_thin, col.regions = '#377eb8', legend = FALSE,
          layer.name = sprintf("Current sample (n = %s)",
                               n_prot_areas_targeted))
mapshot(m, url = file.path("/data/thin-section", 'all-samples-map.html'))
