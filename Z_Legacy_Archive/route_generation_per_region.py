import pandas as pd
import numpy as np
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))  # allow importing traffic_routes_module
from traffic_routes_module import total_duration_peekhour_based

def main(region, regional_stores, Demand, duration_df_index, shift2=False, weekend=False):
    routes_df = route_per_region(region, regional_stores, Demand, duration_df_index, shift2=shift2, weekend=weekend)
    return routes_df


def route_per_region(region, regional_stores, Demand, duration_df_index, shift2=False, weekend=False):
    valid_routes = []

    for store in regional_stores:
        if store == 'region':
            regional_stores.remove(store)

    for start_store in regional_stores:
        for store in regional_stores:
            route = []
            route.append(start_store)

            valid_routes.append({
                'region': region,
                'routes': route,
                'total_demand': Demand[start_store]
            })

            if (Demand[store] + Demand[store]) <= 20 and (store is not start_store):
                route.append(store)
                route_demand = calculate_route_demand(route, Demand)

                for store in regional_stores:
                    if (calculate_route_demand(route, Demand) + Demand[store]) <= 20 and (store not in route):
                        route.append(store)

            route_demand = calculate_route_demand(route, Demand)
            for i in route:
                if i == 'Distribution Centre Auckland':
                    route.remove(i)
            if len(route) > 1 and route_demand <= 20:

                valid_routes.append({
                    'region': region,
                    'routes': route,
                    'total_demand': route_demand
                })

    valid_routes_df = pd.DataFrame(valid_routes)
    # Remove duplicate rows
    #valid_routes_df.drop_duplicates(inplace=True)
    # Drop rows with NaN or infinite values
    valid_routes_df = valid_routes_df.dropna().replace([float('inf'), float('nan')], pd.NA).dropna()
    valid_routes_df = calculate_route_durations_demand(valid_routes_df, Demand, duration_df_index, shift2=shift2, weekend=weekend)

    return valid_routes_df



def calculate_route_durations_demand(routes_df, Demand, duration_df_index, shift2=False, weekend=False):
    route_durations = []
    all_routes = routes_df.iloc[:]['routes']
    regions_all = routes_df.iloc[:]['region']

    index = 0
    for route in all_routes:
        if route != None:
            total_demand = 0
            total_duration = 0
            new_format_route = []
            new_format_route.append('Distribution Centre Auckland')

            for store in route:
                if store != 'Distribution Centre Auckland':
                    total_demand += Demand[store]
                    new_format_route.append(store)
            new_format_route.append('Distribution Centre Auckland')




            for i in range(len(new_format_route) - 1):
                total_duration += duration_df_index.at[new_format_route[i], new_format_route[i+1]]


            total_duration += (total_demand * 600)

            if total_duration > 0:
                route_durations.append({
                    'region': regions_all[index],
                    'routes': new_format_route,
                    'total_duration': total_duration,
                    'total_demand': total_demand
                })
        index += 1

    route_durations_df = pd.DataFrame(route_durations)
    # Bug 3 fix: Apply peak-hour multipliers to reflect 8am vs 2pm shift traffic conditions.
    if not route_durations_df.empty:
        adjusted = total_duration_peekhour_based(
            list(route_durations_df['total_duration']), shift2=shift2, weekend=weekend
        )
        route_durations_df['total_duration'] = adjusted
    return route_durations_df


def calculate_route_demand(route, Demand):
    demand = 0
    if len(route) > 1:
        for store in route:
            if store != 'region' and store != 'routes' and store != 'total_demand':
                demand += Demand[store]
    else:
        demand = Demand[route]
    return demand
