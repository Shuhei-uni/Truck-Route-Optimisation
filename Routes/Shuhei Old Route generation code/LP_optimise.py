import pandas as pd
import numpy as np
from pulp import *
from itertools import permutations


df1 = pd.read_csv('../../00_data/WoolworthsLocations.csv')

Stores = df1['Store']
Latitude = df1['Lat']
Longitude = df1['Long']

store_location_df = pd.DataFrame({
    'Store': Stores,
    'Latitude': Latitude,
    'Longitude': Longitude
})

df2 = pd.read_csv('../../../263NetworkProject/00_data/rounded_weekdays_75th_percentile.csv')
#df2 = pd.read_csv('../../00_data/rounded_weekends_75th_percentile.csv')

df10 = df2['75th Percentile Weekdays']
#df10 = df2['75th Percentile Weekends']


df10 = df10.to_numpy()
Demand = pd.Series(df10, index=Stores[:64])
last_row = pd.Series([0], index=['Distribution Centre Auckland'])
Demand = pd.concat([Demand, last_row])


duration_df = pd.read_csv('../../00_data/WoolworthsDurations.csv')
duration_df.rename(columns={'Unnamed: 0': 'Origin'}, inplace=True)
duration_df_index = duration_df.set_index('Origin')
df3 = duration_df.drop(columns=['Origin'])
duration_matrix = df3.to_numpy()

demand_matrix = Demand.to_numpy()
Demand.replace([np.inf, -np.inf], np.nan, inplace=True)
Demand.fillna(0, inplace=True)

""""
Stores = includes all the store names
- access use of index
Demand = includes the demand of each store
- access use of store name
duration_matrix = includes the distance between each store
- access use of index
duration_df_index = includes the distance between each store
- access use of .at[store name, store name]

"""
def calculate_route_demand(route):
    demand = 0
    if len(route) > 1:
        for store in route:
            demand += Demand[store]
    else:
        demand = Demand[route]
    return demand
def valid_routes(region):
    iteration = 0
    valid_routes = []
    for region_stores in region:
        for start_store in region_stores:

            for store in region_stores:
                route = []
                route.append(start_store)
                if (Demand[store] + Demand[store]) <= 20 and (store is not start_store):
                    route.append(store)
                    for store in region_stores:
                        if (calculate_route_demand(route) + Demand[store]) <= 20 and (store not in route):
                            route.append(store)

                route_demand = calculate_route_demand(route)
                for i in route:
                    if i == 'Distribution Centre Auckland':
                        route.remove(i)
                if len(route) > 1 and route_demand <= 20:
                    valid_routes.append({
                        'routes': route,
                        'total_demand': route_demand
                    })

    valid_routes_df = pd.DataFrame(valid_routes)
    return valid_routes_df

def generate_64_region_based_duration(max_duration):
    regions = []

    for centre_store in Stores:
        region_stores = []
        total_demand_region = 0
        current_max_duration = max_duration

        while total_demand_region < 30:
            for store in Stores:
                store_duration = duration_df_index.at[store, centre_store]
                if store_duration < current_max_duration and store not in region_stores:
                    region_stores.append(store)
                    total_demand_region += Demand[store]

            current_max_duration += 100
        regions.append({
            'stores': region_stores,
            'total_demand_in_region': total_demand_region,
        })
    region_df = pd.DataFrame(regions)
    return region_df

def region_based_coordinate():
    coordinate_region = []

    avg_lat = Latitude.mean()
    avg_long = Longitude.mean()

    nw = []
    ne = []
    sw = []
    se = []
    central = []

    for i in range(len(Stores)):

        lat = Latitude[i]
        long = Longitude[i]
        store = Stores[i]

        x = 0
        y = 0
        m = 0
        n = 0
        c = 0

        if lat > avg_lat and long < avg_long:
            nw.append(store)
            x = 1
        elif lat > avg_lat and long > avg_long:
            ne.append(store)
            y = 1
        elif lat < avg_lat and long < avg_long:
            sw.append(store)
            m = 1
        elif lat < avg_lat and long > avg_long:
            se.append(store)
            n = 1
        else:
            central.append(store)
            c = 1

        if x == 1:
            coordinate_region.append({
                'stores': nw
            })
        elif y == 1:
            coordinate_region.append({
                'stores': ne
            })
        elif m == 1:
            coordinate_region.append({
                'stores': sw
            })

        elif n == 1:
            coordinate_region.append({
                'stores': se
            })
        else:
            coordinate_region.append({
                'stores': central
            })

    return coordinate_region




def remove_duplicate_rows(file_path):
    # Read the CSV file into a DataFrame
    df = pd.read_csv(file_path)

    # Remove duplicate rows
    df.drop_duplicates(inplace=True)
    df = df.drop(columns=df.columns[3])
    # Drop rows with NaN or infinite values
    df = df.dropna().replace([float('inf'), float('nan')], pd.NA).dropna()


    df.to_csv(file_path, index=False)


def calculate_route_durations_demand_1d(routes_df):
    route_durations = []
    all_routes = routes_df.iloc[:]['routes']
    for route in all_routes:
        if route != None:
            total_demand = 0
            total_duration = 0
            new_format_route = []
            new_format_route.append('Distribution Centre Auckland')
            for store in route:
                if store != 'Distribution Centre Auckland':
                    total_duration += 10 * 60
                    total_demand += Demand[store]
                    new_format_route.append(store)
            new_format_route.append('Distribution Centre Auckland')
            for i in range(len(new_format_route) - 1):
                total_duration += duration_df_index.at[new_format_route[i], new_format_route[i+1]]

            if total_duration > 0:
                route_durations.append({
                    'routes': new_format_route,
                    'total_duration': total_duration,
                    'total_demand': total_demand
                })

    route_durations_df = pd.DataFrame(route_durations)
    return route_durations_df


def main():
    file_path = '../../../263NetworkProject/01_routes/Shuhei - generated routes/shuhei_weekdays_routes_combined_need_cleaning.csv'
    #file_path = 'shuhei_weekends_routes_combined_need_cleaning.csv'

    with open(file_path, 'w') as file:
        pass

    min_demand = 10
    max_duration = 50

    regions = generate_64_region_based_duration(max_duration)
    # for i in regions:
    #     print(i)
    region_stores = regions['stores']
    routes_df = valid_routes(region_stores)

    routes_df = calculate_route_durations_demand_1d(routes_df)

    region_2 = region_based_coordinate()
    region_2 = pd.DataFrame(region_2)
    region_stores2 = region_2['stores']
    routes_df2 = valid_routes(region_stores2)
    routes_df2 = calculate_route_durations_demand_1d(routes_df2)

    file_path2 = '../../../263NetworkProject/01_routes/Old_routes_1model_demands/routes2.txt'

    # Read the file and convert each row into a list
    first_routes = []
    routes_data = []
    with open(file_path2, 'r') as file2:
        for line in file2:
            # Convert each row into an array (list in Python)
            route = line.strip().split(',')  # Assuming space-separated values
            first_routes.append(route)

    for route in first_routes:
        demand = 0
        total_duration = 0
        for i in route:
            demand += Demand[i]
        for i in range(len(route) - 1):
            total_duration += duration_df_index.at[route[i], route[i + 1]]

        routes_data.append({
            'routes': route,
            'total_duration': total_duration,
            'total_demand': demand
        })
    routes_df3 = pd.Series(routes_data)

    routes_1 = pd.read_csv('../../../263NetworkProject/01_routes/joe_routes_rounded_weekdays.csv')
    #routes_1 = pd.read_csv('../joe_routes_rounded_weekend.csv')

    routes_2 = pd.read_csv(
        '../../../263NetworkProject/01_routes/Shuhei - generated routes/processed_routes_weekdays.csv')
    #routes_2 = pd.read_csv('processed_routes_weekends.csv')


    combined_df = pd.concat([
        routes_df,
        routes_df2,
        routes_df3,
        routes_1,
        routes_2

    ], ignore_index=True)

    combined_df.to_csv(file_path, index=False)
    remove_duplicate_rows(file_path)


if __name__ == '__main__':
    main()