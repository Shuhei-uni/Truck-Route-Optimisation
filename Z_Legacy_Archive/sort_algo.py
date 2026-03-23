import pandas as pd
import numpy as np
from pulp import *
import ast

def calculate_route_duration(route, Demand, duration_df_index):
    duration = 0
    demand = 0
    for store in route:
        demand += Demand[store]
    for index in range(len(route) - 1):
        store1 = route[index]
        store2 = route[index + 1]
        duration += duration_df_index.at[store1, store2]
    duration += (demand * 600)

    return duration


def sort_to_improve(route, total_duration, Demand, duration_df_index):

    for i in range(len(route) - 1):

        for j in range(1, len(route)):

            test_route = route.copy()
            if test_route[i] != route[0] and test_route[j] != route[0] and i != j:
                temp = route[i]
                test_route[i] = test_route[j]
                test_route[j] = temp

                new_tot_duration = calculate_route_duration(test_route, Demand, duration_df_index)

                if new_tot_duration < total_duration:
                    route = test_route
                    total_duration = new_tot_duration


    return route, total_duration

def remove_zero_demand(route, Demand):
    new_route = []
    for store in route:
        if Demand[store] != 0 or store == 'Distribution Centre Auckland':
            new_route.append(store)
    return new_route

def remove_duplicate_rows(read_file_path, Demand, duration_df_index):
    df = pd.read_csv(read_file_path)


    df.drop_duplicates(inplace=True)
    df2 = []

    for index, row in df.iterrows():
        route = ast.literal_eval(row['routes'])

        route = remove_zero_demand(route, Demand)

        total_duration = calculate_route_duration(route, Demand, duration_df_index)

        new_route, new_duration = sort_to_improve(route, total_duration, Demand, duration_df_index)

        df2.append({
            'region': row['region'],
            'routes': new_route,
            'total_duration': new_duration,
            'total_demand': row['total_demand']
        })

    new_df = pd.DataFrame(df2)
    new_df = new_df[new_df['total_demand'] <= 20]
    new_df = new_df[new_df['total_demand'] > 0]
    #new_df = new_df[new_df['total_duration'] <= 14400]
    return new_df

