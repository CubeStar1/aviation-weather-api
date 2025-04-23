import requests
from bs4 import BeautifulSoup

x= requests.get("https://aviationweather.gov/data/products/sigmet/sigmet_all.gif")
with open("downloaded_image.jpg", "wb") as file:
        file.write(x.content)

y = requests.get("https://www.wpc.ncep.noaa.gov/sfc/namussfc12wbg.gif")
with open("downloaded_image1.jpg", "wb") as file:
        file.write(y.content)

z = requests.get("https://www.1800wxbrief.com/Website/weather/graphic/image?product=SURFACE_ANALYSIS&seed=-1224731316")
with open("downloaded_image2.jpg", "wb") as file:
        file.write(z.content)



