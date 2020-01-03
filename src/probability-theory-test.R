library(tidyverse)

n_population <- 1e6
n_sample <- 1e4

pseudo_int_hash <- round(runif(n_population, -500000, 500000))
pseudo_area <- rexp(n_population, 0.1)

tmp <- tibble(pseudo_int_hash, pseudo_area) %>% 
  mutate(selection_prob = pseudo_area / sum(pseudo_area),
         selector = selection_prob / abs(pseudo_int_hash))

# The version-stable(ish) approach....
areas_approach1 <- tmp %>% 
  arrange(desc(selector)) %>% 
  slice(1:n_sample) %>% 
  pull(pseudo_area)
hist(areas_approach1, breaks = 100) 
# The direct sampling approach.
areas_approach2 <- sample(tmp$pseudo_area, n_sample, prob = tmp$selection_prob)
hist(areas_approach2, breaks = 100)

d <- bind_rows(tibble(area = areas_approach1, approach = 1),
               tibble(area = areas_approach2, approach = 2))
ggplot(d) +
  geom_density(aes(x = area, group = approach, color = factor(approach))) +
  scale_color_brewer("Approach", type = "qual", palette = "Set1")
