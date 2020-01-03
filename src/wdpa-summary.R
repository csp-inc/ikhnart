library(tidyverse)
library(lubridate)
library(ggthemes)
source('src/utils.R')

paste0("gsutil -m cp -r gs://site-", unique(wdpa_shp_thin$WDPAID), " data/thin-section") %>%
  paste(collapse = " && ") %>% cat



lapply(314748, function(focal_id) {  # unique(wdpa_shp_thin$WDPAID)

  # focal_id <- 314748  # 555586306
  
  # system(sprintf("sh run-gsutil-one-off.sh %s", focal_id))
  elev_csv <- list.files(sprintf("data/thin-section/site-%s", focal_id),
                         pattern = "ELEVATION", recursive = TRUE, full.names = TRUE)
  elev_data <- read_csv(elev_csv)
  
  land_cov_csv <- list.files(sprintf("data/thin-section/site-%s", focal_id),
                             pattern = "MCD12Q1", recursive = TRUE, full.names = TRUE)
  land_cov_data_raw <- read_csv(land_cov_csv)
  
  land_cov_data <- land_cov_data_raw %>%
    mutate(year = year(img_date)) %>% 
    group_by(location) %>% 
    summarise_at(vars(matches("LC_Type")), list(~ n_distinct(.), ~ getmode(as.integer(.)))) %>% 
    select(location, matches("mode"))
  
  
  loc_csv <- list.files("data/thin-section/random-samples",
                        pattern = as.character(focal_id), 
                        recursive = TRUE, full.names = TRUE)
  loc_data <- read_csv(loc_csv)
  loc_sf <- st_as_sf(loc_data, coords = c("X", "Y"), crs = 4326)
  
  vi_csv <- list.files(sprintf("data/thin-section/site-%s", focal_id),
                       pattern = "LANDSAT", recursive = TRUE, full.names = TRUE)
  vi_data_raw <- read_csv(vi_csv)
  
  vi_data_raw %>% group_by(location) %>% tally()
  
  vi_data <- vi_data_raw %>% 
    mutate(doy = yday(img_date), 
           year = year(img_date),
           decade = decade_for_year(year),
           dec_doy = decimal_date(img_date) %% year,
           rel_year_in_decade = year - decade,
           rel_dec_year_in_decade = rel_year_in_decade + dec_doy) #%>% 
  vi_data %>% left_join(elev_data) %>% pull(elevation) %>% range
  # browser()
  ggplot(vi_data %>% 
           left_join(elev_data) %>% 
           left_join(land_cov_data)) +
    facet_grid(decade~.) +
    geom_point(aes(x = rel_dec_year_in_decade, y = EVI, 
                   # color = factor(LC_Type1_getmode)), 
                   color = as.numeric(elevation)),
               alpha = 0.1) +
    # scale_color_brewer("Land cover", type = "qual", palette = "Set1") +
    scale_color_viridis_c("Elevation") +
    theme_hc() +
    labs(x = 'Year (in decade)', y = "VI") +
    theme(legend.key.width = unit(3, "cm"))
  ggsave(file.path("data/thin-section/plots", paste0(focal_id, ".png")),
         width = 16, height = 9)
  
  # ggplot(d_sim_with_bonus_date_info) +
  #   facet_grid(decade~.) +
  #   geom_line(aes(x = rel_dec_year_in_decade, y = y_hat, group = j, color = factor(j))) +
  #   geom_point(data = d_sim_with_bonus_date_info \%>\% filter(!is.na(date)),
  #              aes(x = rel_dec_year_in_decade, y = y, fill = factor(j)), alpha = .8, size = 1.1,
  #              pch = 21) +
  #   theme_hc(base_size = 13) +
  #   scale_color_hc(name = "Site (index)") +
  #   scale_fill_hc() +
  #   guides(fill = FALSE) +
  #   labs(x = 'Year (in decade)', y = expression(hat(y)))
  browser()
  mapview(filter(wdpa_shp_thin, WDPAID == focal_id)) +
    mapview(loc_sf)
})


