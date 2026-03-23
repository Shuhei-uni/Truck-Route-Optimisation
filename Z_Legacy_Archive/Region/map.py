import folium
import pandas as pd

# Load the CSV file
file_path = '../0_Fixed Data - Initial Setup data/WoolworthsLocations.csv'
data = pd.read_csv(file_path)

# Define the latitude and longitude bounds for Auckland
north = -36.8408  # Northern latitude
south = -36.9150  # Southern latitude
east = 174.8600   # Eastern longitude
west = 174.7300   # Western longitude

# Calculate the center of the bounding box
center_lat = (north + south) / 2
center_lon = (east + west) / 2

# Create a map centered at the calculated midpoint
m = folium.Map(location=[center_lat, center_lon], zoom_start=13)

# Add a rectangle to indicate the specified bounds
folium.Rectangle(
    bounds=[[south, west], [north, east]],
    color="blue",
    fill=True,
    fill_opacity=0.2
).add_to(m)

# Add markers for each store location
for _, row in data.iterrows():
    folium.Marker(
        location=[row['Lat'], row['Long']],
        popup=row['Store'],
        icon=folium.Icon(color='red', icon='info-sign')
    ).add_to(m)

for _, row in data.iterrows():
    # Determine marker color based on store name
    marker_color = 'black' if row['Store'] == 'Distribution Centre Auckland' else 'red'

    folium.Marker(
        location=[row['Lat'], row['Long']],
        popup=row['Store'],
        icon=folium.Icon(color=marker_color, icon='info-sign')
    ).add_to(m)

# Save the map to an HTML file
m.save("auckland_stores_map.html")

# Display the map
