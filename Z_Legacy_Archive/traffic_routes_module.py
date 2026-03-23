import pandas as pd
import numpy as np
import random
from itertools import combinations, permutations
import sys
import os


def routes_for_region(demands, shop_names, all_names):
    """
    Generate routes for regions with changed demands and durations.
    Return a pandas DataFrame containing the routes, total demands, and the total durations.
    """
    routes = []
    tot_dem = []
    indices = [all_names.index(store) for store in shop_names]
    non_zero_indices = [i for i in indices if demands[i] > 0]

    for r in range(1, len(shop_names) + 1):  # Start from 1 to avoid empty routes
        for combo_indices in combinations(non_zero_indices, r):
            route = [all_names[i] for i in combo_indices]
            total_demand = sum(demands[i] for i in combo_indices)
            if 0 < total_demand <= 20:
                for lots_route in permutations(route):
                    current_route = ('Distribution Centre Auckland',) + lots_route + ('Distribution Centre Auckland',)
                    routes.append(list(current_route))
                    tot_dem.append(total_demand)

    return routes, tot_dem


def calculate_durations(routes, durations, demands, all_names):
    total_durations = []
    for route, total_demand in zip(routes, demands):
        tot_dur = 0
        for j in range(len(route) - 1):
            ind1 = all_names.index(route[j])
            ind2 = all_names.index(route[j + 1])
            duration = durations.iloc[ind1, ind2 + 1]
            tot_dur += duration
        tot_dur += total_demand * 600
        total_durations.append(tot_dur)
    return total_durations


def all_routes(all_names, demands, shop_names, durations, shift2=False, weekend=False):
    routes, total_demands = routes_for_region(demands, shop_names, all_names)
    total_durations = calculate_durations(routes, durations, total_demands, all_names)
    # total_durations = total_duration_peekhour_based(total_durations, shift2, weekend)
    routes_df = pd.DataFrame({
        'routes': routes,
        'total_duration': total_durations,
        'total_demand': total_demands
    })
    return routes_df


def durations_traffic_based(durations):
    """
    write all new durations in another csv file.
    """

    durations_traffic = durations.copy()
    for i in range(len(durations)):
        for j in range(len(durations.columns) - 1):
            duration = durations.iloc[i, j + 1]
            if duration != 0:
                if 1200 <= duration <= 1800:
                    new_duration = random.gauss(duration, 720)
                    durations_traffic.iat[i, j + 1] = new_duration
                elif duration > 1800:
                    new_duration = random.gauss(duration, 900)
                    durations_traffic.iat[i, j + 1] = new_duration
                elif duration < 1200:
                    new_duration = random.gauss(duration, 360)
                    durations_traffic.iat[i, j + 1] = new_duration
    durations_traffic.to_csv('Durations_traffic_based.csv', index=False)
    file_path = 'Durations_traffic_based.csv'
    return file_path


def total_duration_peekhour_based(total_durations, shift2=False, weekend=False):
    """
    Modify total_duration based on peak hour conditions.
    """
    for i in range(len(total_durations)):
        if weekend is False:
            if shift2 is False and total_durations[i] > 3600:
                total_durations[i] *= 1.1  # 10% increase for peak hour
            elif shift2 is True and total_durations[i] > 7200:
                total_durations[i] *= 1.2  # 20% increase for peak hour
    return total_durations
