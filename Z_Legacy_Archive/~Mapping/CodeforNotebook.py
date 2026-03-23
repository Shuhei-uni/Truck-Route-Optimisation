ORSkey = '5b3ce3597851110001cf6248128a3241c07c413d98ac172c16d50a81' # this is my unique key generated from openstreetmaps

import numpy as np
import pandas as pd
import folium
locations = pd.read_csv("../0_Fixed Data - Initial Setup data/WoolworthsLocations.csv")
coords = locations[['Long', 'Lat']] # ~Mapping packages work with Long, Lat arrays
coords = coords.to_numpy().tolist() # Make the arrays into a list of lists.
# Folium, however, requires Lat, Long arrays - so a reversal is needed.
m = folium.Map(location = list(reversed(coords[2])), zoom_start=10)
# NOT RUN, to plot first store.
# folium.Marker(list(reversed(coords[0])), popup = locations.Store[0], icon = folium. ,→Icon(color = 'black')).add_to(m)

for i in range(0, len(coords)):
    if locations.Type[i] == "SuperValue":
        iconCol = "red"
    elif locations.Type[i] == "Woolworths":
        iconCol = "green"
    elif locations.Type[i] == "Distribution Centre":
        iconCol = "black"
    elif locations.Type[i] == "Metro":
        iconCol = "orange"
    elif locations.Type[i] == "FreshChoice":
        iconCol = "blue"
    folium.Marker(list(reversed(coords[i])), popup = locations.Store[i], icon = folium.Icon(color = iconCol)).add_to(m)

m

# Note - to run this in Jupyter Notebook, make sure all packages are downloaded including folium

# The rest of the code is on the Notebook
