import pandas as pd
import numpy as np
from pulp import *

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
df10 = df2['75th Percentile Weekdays']
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



"""

1. hardcode regions:
    
    make regions based on lat and long coordinates
    make 64 regions based on duration from start node
        - only include stores with duration < 2000
    regions:
        - total demand from all the stores within the region should be close to 20 * num_trucks
            maximise the num demand <= 20 * num_trucks
        - minimise the total duration within the region
    
    while  num_stores = num_routes : so generate the same number of routes 
    for store in Stores:
        
        - Dont consider overlaps in this function

        LP route generation : Objective : Minimizing the duration
            Objective : Mminimize to find the lowest duration
            - LP variables are binary
            constraint : the demand up to 20
        
        given the stores find the optimal order to visit each stores and back to the distribution centre
        
        LP route generation : Objective : Maximise the demand
            Objective : maximise the total demand
            Constraints : 20 max dem
            constaints : cant select same store twice
        
        given the stores find the optimal order to visit each stores and back to the distribution centre
            
        LP route generation : Objective : visit the most extreme lat/long coordinates within region
            Objective : 
    
    Overall goal
        - generate 
            
"""
def find_routes_min_duratioin(regions, min_demand):
    routes = []
    for region in regions:
        region_stores = region['stores']
        if not region_stores:
            continue

        prob = LpProblem("Minimize_Duration", LpMinimize)
        x = LpVariable.dicts("x", (region_stores, region_stores), 0, 1, LpBinary)
        prob += lpSum(duration_df_index.at[i, j] * x[i][j] for i in region_stores for j in region_stores if i != j)
        prob += lpSum([Demand[j] * x[i][j] for i in region_stores for j in region_stores if i != j]) <= 20
        prob += lpSum([Demand[j] * x[i][j] for i in region_stores for j in region_stores if i != j]) >= min_demand

        prob.solve(PULP_CBC_CMD(msg=False))

        route = []
        for i in region_stores:
            for j in region_stores:
                if i != j and x[i][j].varValue == 1:
                    route.append((i, j))

        routes.append({
            'routes': route,
        })

    return routes

def find_routes_max_stores(regions, min_demand):
    routes = []
    for region in regions:
        region_stores = region['stores']
        if not region_stores:
            continue

        prob = LpProblem("Maximize_Stores_Visited", LpMaximize)
        x = LpVariable.dicts("x", (region_stores, region_stores), 0, 1, LpBinary)

        # Objective: Maximize the number of stores visited
        prob += lpSum(x[i][j] for i in region_stores for j in region_stores if i != j)

        # Constraints
        prob += lpSum(
            duration_df_index.at[i, j] * x[i][j] for i in region_stores for j in region_stores if i != j) <= 20
        prob += lpSum(Demand[j] * x[i][j] for i in region_stores for j in region_stores if i != j) >= min_demand

        prob.solve(PULP_CBC_CMD(msg=False))

        route = []
        for i in region_stores:
            for j in region_stores:
                if i != j and x[i][j].varValue == 1:
                    route.append((i, j))

        routes.append({
            'routes': route,
        })

    return routes
def find_routes_max_demand_2D(regions):
    routes = []
    for region in regions:
        region_stores = region['stores']
        if not region_stores:
            continue

        prob = LpProblem("Maximize_Total_Demand", LpMaximize)
        x = LpVariable.dicts("x", (region_stores, region_stores), 0, 1, LpBinary)

        # Objective: Maximize the total demand
        prob += lpSum(Demand[j] * x[i][j] for i in region_stores for j in region_stores if i != j)

        # Constraints
        prob += lpSum(Demand[j] * x[i][j] for i in region_stores for j in region_stores if i != j) <= 20
        prob += lpSum(x[i][j] for i in region_stores for j in region_stores if i != j) <= len(region_stores) - 1

        prob.solve(PULP_CBC_CMD(msg=False))

        route = []
        for i in region_stores:
            for j in region_stores:
                if i != j and x[i][j].varValue == 1:
                    route.append((i, j))

        routes.append({
            'routes': route,
        })

    return routes

def find_routes_min_duration_1d(regions, min_demand):
    routes = []
    for region in regions:
        region_stores = region['stores']
        if not region_stores:
            continue

        visited = [False] * len(region_stores)
        non_visited = 100
        loop_count = 0
        while loop_count < len(region_stores) - 5 and non_visited > 3:
            prob = LpProblem("Minimize_Duration", LpMinimize)
            x = LpVariable.dicts("x", range(len(region_stores)), 0, 1, LpBinary)

            # Objective: Minimize the total duration
            prob += lpSum(duration_df_index.at[region_stores[i], region_stores[j]] * x[j] for i in range(len(region_stores)) for j in range(len(region_stores)) if i != j)

            # Constraints
            prob += lpSum(Demand[region_stores[j]] * x[j] for j in range(len(region_stores))) <= 20
            prob += lpSum(Demand[region_stores[j]] * x[j] for j in range(len(region_stores))) >= min_demand

            prob.solve(PULP_CBC_CMD(msg=False))

            route = []
            for j in range(len(region_stores)):
                if x[j].varValue == 1:
                    route.append(region_stores[j])
                    visited[j] = True
            routes.append({
                'routes': route,
            })

            non_visited = len([store for store in visited if not store])
            loop_count += 1

    return routes

def find_routes_max_stores_1d(regions, min_demand):
    routes = []
    for region in regions:
        region_stores = region['stores']
        if not region_stores:
            continue

        visited = [False] * len(region_stores)
        non_visited = 100
        loop_count = 0
        while loop_count < len(region_stores) - 5 and non_visited > 3:
            prob = LpProblem("Maximize_Stores_Visited", LpMaximize)
            x = LpVariable.dicts("x", range(len(region_stores)), 0, 1, LpBinary)

            # Objective: Maximize the number of stores visited
            prob += lpSum(x[j] for j in range(len(region_stores)))

            # Constraints
            prob += lpSum(Demand[region_stores[j]] * x[j] for j in range(len(region_stores))) <= 20
            prob += lpSum(Demand[region_stores[j]] * x[j] for j in range(len(region_stores))) >= min_demand

            prob.solve(PULP_CBC_CMD(msg=False))

            route = []
            for j in range(len(region_stores)):
                if x[j].varValue == 1:
                    route.append(region_stores[j])
                    visited[j] = True
            routes.append({
                'routes': route,
            })
            non_visited = len([store for store in visited if not store])
            loop_count += 1


    return routes

def find_routes_max_demand_1D(regions):
    routes = []
    for region in regions:
        region_stores = region['stores']
        if not region_stores:
            continue

        visited = [False] * len(region_stores)
        non_visited = 100
        loop_count = 0
        while loop_count < len(region_stores) - 5 and non_visited > 3:
            prob = LpProblem("Maximize_Total_Demand", LpMaximize)
            x = LpVariable.dicts("x", range(len(region_stores)), 0, 1, LpBinary)

            # Objective: Maximize the total demand
            prob += lpSum(Demand[region_stores[j]] * x[j] for j in range(len(region_stores)))

            # Constraints
            prob += lpSum(Demand[region_stores[j]] * x[j] for j in range(len(region_stores))) <= 20
            prob += lpSum(x[j] for j in range(len(region_stores))) <= len(region_stores) - 1

            # Add constraint to ensure visited stores cannot be visited again
            for j in range(len(region_stores)):
                if visited[j]:
                    prob += x[j] == 0

            prob.solve(PULP_CBC_CMD(msg=False))

            route = []
            for j in range(len(region_stores)):
                if x[j].varValue == 1:
                    route.append(region_stores[j])
                    visited[j] = True
            routes.append({
                'routes': route,
            })
            non_visited = len([store for store in visited if not store])
            loop_count += 1
    return routes

def visit_node_once():
    routes = []

    for store in Stores:
        if store != 'Distribution Centre Auckland':
            route = [store]

            routes.append({
                'routes': route,
            })

    return routes

def generate_64_region_based_duration(max_duration=2000):
    regions = []

    for centre_store in Stores:
        region_stores = []
        total_demand_region = 0
        current_max_duration = max_duration

        while total_demand_region < 40 and len(region_stores) < 15:
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

    return regions

def sort_to_improve(route, total_duration):

    """
    Switch up the order of the stores in the route to see if the total duration can be reduced

    :param route: array
    :param total_duration: total_current_duration
    :return: new_route, new_total_duration
    """
    for i in range(1,len(route)-1):
        if route[i] == 'Distribution Centre Auckland':
            route.pop(i)


    for i in range(1, len(route) - 1):

        for j in range(1, len(route)):

            test_route = route.copy()
            if test_route[i] != route[0] and test_route[j] != route[0] and i != j:
                temp = route[i]
                test_route[i] = test_route[j]
                test_route[j] = temp

                new_tot_duration = 0
                for index in range(len(route) - 1):
                    store1 = test_route[index]
                    store2 = test_route[index+1]
                    new_tot_duration += duration_df_index.at[store1,store2]

                if new_tot_duration < total_duration:
                    route = test_route
                    total_duration = new_tot_duration


    return route, total_duration

def calculate_route_durations_demand_2d(rough_routes_df):
    route_durations = []

    for route_info in rough_routes_df:
        route_list = route_info['routes']

        for route_tuple in route_list:
            if route_tuple != None:
                total_duration = 0
                total_demand = 0
                new_format_route = []
                new_format_route.append('Distribution Centre Auckland')
                for i in range(len(route_tuple)):
                    if route_tuple[i] != 'Distribution Centre Auckland':
                        total_duration += 10 * 60
                        total_demand += Demand[route_tuple[i]]
                        new_format_route.append(route_tuple[i])
                new_format_route.append('Distribution Centre Auckland')
                for i in range(len(new_format_route) - 1):
                    total_duration += duration_df_index.at[new_format_route[i], new_format_route[i+1]]

                new_format_route, total_duration = sort_to_improve(new_format_route, total_duration)

                if total_duration > 0:
                    route_durations.append({
                        'routes': new_format_route,
                        'total_duration': total_duration,
                        'total_demand': total_demand
                    })

    route_durations_df = pd.DataFrame(route_durations)
    return route_durations_df

def calculate_route_durations_demand_1d(rough_routes_df):
    route_durations = []

    for route_info in rough_routes_df:
        route = route_info['routes']
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

            new_format_route, total_duration = sort_to_improve(new_format_route, total_duration)
            if total_duration > 0:
                route_durations.append({
                    'routes': new_format_route,
                    'total_duration': total_duration,
                    'total_demand': total_demand
                })

    route_durations_df = pd.DataFrame(route_durations)
    return route_durations_df

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
    df = df.dropna().replace([float('inf'), float('nan')], pd.NA).dropna()


    # Save the cleaned DataFrame back to the CSV file
    df.to_csv(file_path, index=False)

def main():
    file_path = '../../../263NetworkProject/01_routes/Shuhei - generated routes/processed_routes_weekdays.csv'
    with open(file_path, 'w') as file:
        pass

    min_demand = 0
    max_duration = 800

    regions = generate_64_region_based_duration(max_duration)

    region_route_df_2d = find_routes_min_duratioin(regions, min_demand)
    region_route_df_2d = calculate_route_durations_demand_2d(region_route_df_2d)

    routes_max_stores_df_2d = find_routes_max_stores(regions, min_demand)
    routes_max_stores_df_2d = calculate_route_durations_demand_2d(routes_max_stores_df_2d)

    routes_max_demand_df_2d = find_routes_max_demand_2D(regions)
    routes_max_demand_df_2d = calculate_route_durations_demand_2d(routes_max_demand_df_2d)

    routes_max_demand_df_1d = find_routes_max_demand_1D(regions)
    routes_max_demand_df_1d = calculate_route_durations_demand_1d(routes_max_demand_df_1d)

    region_route_df_1d = find_routes_min_duration_1d(regions, min_demand)
    region_route_df_1d = calculate_route_durations_demand_1d(region_route_df_1d)

    routes_max_stores_df_1d = find_routes_max_stores_1d(regions, min_demand)
    routes_max_stores_df_1d = calculate_route_durations_demand_1d(routes_max_stores_df_1d)

    ################################
    region_coordinate_1 = region_based_coordinate()

    region_route_df_2d_1 = find_routes_min_duratioin(region_coordinate_1, min_demand)
    region_route_df_2d_1 = calculate_route_durations_demand_2d(region_route_df_2d_1)

    routes_max_stores_df_2d_1 = find_routes_max_stores(region_coordinate_1, min_demand)
    routes_max_stores_df_2d_1 = calculate_route_durations_demand_2d(routes_max_stores_df_2d_1)

    routes_max_demand_df_2d_1 = find_routes_max_demand_2D(region_coordinate_1)
    routes_max_demand_df_2d_1 = calculate_route_durations_demand_2d(routes_max_demand_df_2d_1)

    routes_max_demand_df_1d_1 = find_routes_max_demand_1D(region_coordinate_1)
    routes_max_demand_df_1d_1 = calculate_route_durations_demand_1d(routes_max_demand_df_1d_1)

    region_route_df_1d_1 = find_routes_min_duration_1d(region_coordinate_1, min_demand)
    region_route_df_1d_1 = calculate_route_durations_demand_1d(region_route_df_1d_1)

    routes_max_stores_df_1d_1 = find_routes_max_stores_1d(region_coordinate_1, min_demand)
    routes_max_stores_df_1d_1 = calculate_route_durations_demand_1d(routes_max_stores_df_1d_1)

    #########################
    # visit node once
    once_df = visit_node_once()
    once_df = calculate_route_durations_demand_1d(once_df)


    # Concatenate all dataframes into a single dataframe
    combined_df = pd.concat([
        region_route_df_2d,
        routes_max_stores_df_2d,
        routes_max_demand_df_2d,
        routes_max_demand_df_1d,
        region_route_df_1d,
        routes_max_stores_df_1d,
        region_route_df_2d_1,
        routes_max_stores_df_2d_1,
        routes_max_demand_df_2d_1,
        routes_max_demand_df_1d_1,
        region_route_df_1d_1,
        routes_max_stores_df_1d_1,
        once_df
    ], ignore_index=True)


    combined_df.to_csv(file_path, index=False)
    remove_duplicate_rows(file_path)


if __name__ == '__main__':
    main()