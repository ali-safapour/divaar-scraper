# Possible values are: car, realestate
scrape_content_type = 'car'

# The city you want to scrape the data from
city = 'tehran'

download_images = False

# Headless mode lets you to run the browser without GUI. 
# It is appropriate solution for:
# 1 - Servers 
# 2 - Computers with low RAM
# 3 - People who want to use their computers when 
# the scraping is in progress.
headless_mode = True

# If you want to save the browser cache.
keep_driver_cache = True

# Images won't be loaded to speed up the scraping process. Recommendation value
# is always True (This option won't interrupt the downloading of images if you
# set download_images option to True)
disable_loading_images = True

# Politeness
delay_between_requests = 0.5

