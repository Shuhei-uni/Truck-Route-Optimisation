import pandas as pd
import numpy as np
from pulp import *
import ast




filepath = '../routes_per_region_unfiltered.csv'



df1 = pd.read_csv('../../0_Fixed Data - Initial Setup data/WoolworthsLocations.csv')
Stores = df1['Store']
Latitude = df1['Lat']
Longitude = df1['Long']

store_location_df = pd.DataFrame({
    'Store': Stores,
    'Latitude': Latitude,
    'Longitude': Longitude
})

df2 = pd.read_csv('../../0_Fixed Data - Initial Setup data/storemean.csv')
#df2 = pd.read_csv('../../../263NetworkProject/00_data/rounded_weekends_75th_percentile.csv')

#df10 = df2['75th Percentile Weekdays']
df10 = df2['Weekday Mean']


df10 = df10.to_numpy()
Demand = pd.Series(df10, index=Stores[:64])
last_row = pd.Series([0], index=['Distribution Centre Auckland'])
Demand = pd.concat([Demand, last_row])


duration_df = pd.read_csv('../../0_Fixed Data - Initial Setup data/WoolworthsDurations.csv')
duration_df.rename(columns={'Unnamed: 0': 'Origin'}, inplace=True)
duration_df_index = duration_df.set_index('Origin')
df3 = duration_df.drop(columns=['Origin'])
duration_matrix = df3.to_numpy()

demand_matrix = Demand.to_numpy()
Demand.replace([np.inf, -np.inf], np.nan, inplace=True)
Demand.fillna(0, inplace=True)


def main():
    readfile = '../routes_per_region_unfiltered.csv'
    writefile = '../routes_per_region_filtered.csv'


    remove_duplicate_rows(readfile, writefile)



def calculate_route_duration(route):
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


def sort_to_improve(route, total_duration):

    for i in range(len(route) - 1):

        for j in range(1, len(route)):

            test_route = route.copy()
            if test_route[i] != route[0] and test_route[j] != route[0] and i != j:
                temp = route[i]
                test_route[i] = test_route[j]
                test_route[j] = temp

                new_tot_duration = calculate_route_duration(test_route)

                if new_tot_duration < total_duration:
                    route = test_route
                    total_duration = new_tot_duration


    return route, total_duration

def remove_zero_demand(route):
    new_route = []
    for store in route:
        if Demand[store] != 0 or store == 'Distribution Centre Auckland':
            new_route.append(store)
    return new_route

def remove_duplicate_rows(read_file_path, write_file_path):
    # Read the CSV file into a DataFrame
    df = pd.read_csv(read_file_path)
    file2 = write_file_path
    #file2 = '../Overall_Rounded_Final_Routes_Weekends.csv'

    with open(file2, 'w') as f:
        f.close()

    df.drop_duplicates(inplace=True)

    df2 = []

    for index, row in df.iterrows():
        route = ast.literal_eval(row['routes'])

        route = remove_zero_demand(route)

        total_duration = calculate_route_duration(route)

        new_route, new_duration = sort_to_improve(route, total_duration)

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
    new_df.to_csv(file2, index=False)


if __name__ == '__main__':
    main()