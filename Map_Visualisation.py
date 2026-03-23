"""
Map_Visualisation.py
====================
Generates an interactive HTML map showing the optimal routes from the master schedule.
Uses Folium with free OpenStreetMap tiles (no API key required).

Usage:
    python Map_Visualisation.py
    python Map_Visualisation.py --master "Fixed Routes - Final/master_schedule.csv"

Outputs:
    Fixed Routes - Final/routes_map.html
"""

import ast
import argparse
import pandas as pd
import folium
import os

def load_locations(locations_csv: str = '0_Fixed Data - Initial Setup data/WoolworthsLocations.csv') -> dict:
    """Load store locations into a dictionary of {store_name: (lat, lon)}."""
    df = pd.read_csv(locations_csv)
    locs = {}
    for _, row in df.iterrows():
        name = row['Store']
        # The master schedule removes 'Distribution Centre ' sometimes, or uses exact name.
        # Let's keep exact names from the CSV.
        locs[name] = (row['Lat'], row['Long'])
    return locs

def generate_map(master_csv: str = 'Fixed Routes - Final/master_schedule.csv',
                 locations_csv: str = '0_Fixed Data - Initial Setup data/WoolworthsLocations.csv',
                 outdir: str = 'Fixed Routes - Final'):
    
    if not os.path.exists(master_csv):
        print(f"Error: Master schedule not found at {master_csv}. Run Global_LP.py first.")
        return

    # Load data
    master_df = pd.read_csv(master_csv)
    locations = load_locations(locations_csv)
    
    # Depot location is the center of the map
    depot_name = 'Distribution Centre Auckland'
    if depot_name in locations:
        map_center = locations[depot_name]
    else:
        map_center = [-36.8485, 174.7633] # Auckland CBD default
        print(f"Warning: {depot_name} not found in locations CSV.")

    # Create base map, dark theme (CartoDB dark_matter) to match our UI, or standard OSM
    # Using OpenStreetMap since it's default and colorful, but CartoDB dark_matter is sleeker
    m = folium.Map(location=map_center, zoom_start=11, tiles='CartoDB dark_matter')

    # Add Depot Marker
    if depot_name in locations:
        folium.Marker(
            location=locations[depot_name],
            popup='<b>Distribution Centre (Depot)</b>',
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(m)

    # Color palette for routes based on region or index to differentiate them
    colors = [
        '#388bfd', '#2ea043', '#f0c040', '#bc8cff', 
        '#ff7b72', '#79c0ff', '#56d364', '#e2e2e2',
        'orange', 'purple', 'lightblue', 'lightgreen', 'pink'
    ]

    # Keep track of which stores we've added a marker for to avoid duplicates
    added_markers = set([depot_name])

    route_idx = 0
    for _, row in master_df.iterrows():
        route_list = ast.literal_eval(row['route'])
        is_ww = row['assigned_to'] == 'WW'
        
        # We only want to draw WW routes or distinguish MF routes?
        # Let's draw all but distinguish them. Mainfreight is dashed red.
        
        # Build coordinate list for the line
        coords = []
        for store in route_list:
            if store in locations:
                coords.append(locations[store])
                
                # Add store marker if not already added
                if store not in added_markers:
                    folium.CircleMarker(
                        location=locations[store],
                        radius=5,
                        popup=f"<b>{store}</b>",
                        color='white',
                        fill=True,
                        fill_color='#388bfd' if is_ww else '#e94560',
                        fill_opacity=1.0
                    ).add_to(m)
                    added_markers.add(store)
            else:
                print(f"Warning: Location for {store} not found in {locations_csv}")

        # Draw the route line
        if len(coords) > 1:
            if is_ww:
                line_color = colors[route_idx % len(colors)]
                weight = 3
                dash_array = None
                opacity = 0.8
            else:
                line_color = '#e94560' # Mainfreight red
                weight = 2
                dash_array = '5, 5' # Dashed line
                opacity = 0.7
                
            region = row['region']
            tooltip_txt = f"{row['assigned_to']} Route (R{region})<br>Stores: {len(route_list)-1}<br>Demand: {row['demand']} pal"
            
            folium.PolyLine(
                coords,
                color=line_color,
                weight=weight,
                opacity=opacity,
                dash_array=dash_array,
                tooltip=tooltip_txt
            ).add_to(m)
            
            if is_ww:
                route_idx += 1

    os.makedirs(outdir, exist_ok=True)
    out_path = os.path.join(outdir, 'routes_map.html')
    m.save(out_path)
    print(f"  Interactive map saved to: {out_path}")
    return out_path

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Woolworths Interactive Map Generator')
    parser.add_argument('--master', type=str, default='Fixed Routes - Final/master_schedule.csv')
    parser.add_argument('--locs', type=str, default='0_Fixed Data - Initial Setup data/WoolworthsLocations.csv')
    parser.add_argument('--out', type=str, default='Fixed Routes - Final')
    args = parser.parse_args()

    print(f"\n{'='*52}")
    print(f"  Generating interactive map → {args.out}/routes_map.html")
    print(f"{'='*52}")
    
    generate_map(args.master, args.locs, args.out)
    print(f"\n  Done. Open routes_map.html in any web browser.")
    print(f"{'='*52}\n")
