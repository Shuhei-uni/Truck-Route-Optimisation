import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
import ast

# Load the CSV files into DataFrames
routes_file_path = '../Fixed Routes - Final/all_regions_routes_selected_weekdays.csv'
locations_file_path = '../0_Fixed Data - Initial Setup data/WoolworthsLocations.csv'


# Load the CSV file for store locations
woolworths_data = pd.read_csv(locations_file_path)

# Load the routes from the CSV file outputted from the optimization problem
selected_routes_df = pd.read_csv(routes_file_path)

routes = selected_routes_df['routes'].apply(eval).tolist()  # Convert string representation to list

# Extract latitude and longitude
latitudes = woolworths_data['Lat']
longitudes = woolworths_data['Long']
stores = woolworths_data['Store']

# Create a mapping from store names to their coordinates
store_coords = {store: (longitudes[i], latitudes[i]) for i, store in enumerate(stores)}

# Plot the data
plt.figure(figsize=(12, 10))
plt.scatter(longitudes, latitudes, c='blue', marker='o', edgecolor='k')
plt.title('Woolworths Store Locations and Routes')
plt.xlabel('Longitude')
plt.ylabel('Latitude')

# Annotate the points with store names
for i, store in enumerate(stores):
    plt.annotate(store, (longitudes[i], latitudes[i]), fontsize=8, alpha=0.75)

# Plot each route with a different color
colors = plt.cm.get_cmap('tab20', len(routes))  # Get a colormap with enough colors

for idx, route in enumerate(routes):
    color = colors(idx)
    for i in range(len(route) - 1):
        start = store_coords[route[i]]
        end = store_coords[route[i+1]]
        plt.plot([start[0], end[0]], [start[1], end[1]], color=color, linewidth=2, alpha=0.7)


# Add grid lines
plt.grid(True)
plt.savefig('mappings/region1_weekday_.png')

plt.show()