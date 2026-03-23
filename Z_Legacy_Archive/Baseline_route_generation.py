import pandas as pd
import numpy as np
#from traffic_routes_module import *
from LP_Simulation_Select_Route_Region import *
from Routes.route_generation_per_region import *
from Routes.sort_algo import *

def main():

    """
    Change this to get weekday or saturday data, this is the only change you need to make!!
    """
    weekday = True

    if weekday == True:
        simulation_demand_data = pd.read_csv('../0_Fixed Data - Initial Setup data/weekday_mean_demand.csv')
        final_file_name = '../Fixed Routes - Final/weekday_mean_data.csv'
    else:
        simulation_demand_data = pd.read_csv('../0_Fixed Data - Initial Setup data/saturday_mean_demand.csv')
        final_file_name = '../Fixed Routes - Final/saturday_mean_data.csv'
    ###################################################################

    data = []
    regional = []

    (AllStores, traffic_duration_df, all_region_info,
     regions, num_trucks_per_cluster) = load_all_data()

    Demand = pd.Series(simulation_demand_data['1'].to_numpy(), index=AllStores[:64])
    last_row = pd.Series([0], index=['Distribution Centre Auckland'])
    Demand = pd.concat([Demand, last_row])

    all_routes = []
    for region in regions:
        route = []

        number_trucks_region = num_trucks_per_cluster[region]

        regional_data = all_region_info[all_region_info['Cluster'] == region]
        regional_stores = regional_data['Store']


        day_routes_df = route_per_region(region, regional_stores, Demand, traffic_duration_df)
        day_all_routes_df = pd.DataFrame(day_routes_df)


        temp_file_saved = 'tempfile.csv'
        day_all_routes_df.to_csv(temp_file_saved, index=False)
        day_all_routes_df = remove_duplicate_rows(temp_file_saved, Demand, traffic_duration_df)
        day_all_routes_df.to_csv(temp_file_saved, index=False)
        day_selected_routes_df = selecting_routes_per_region(temp_file_saved, region, number_trucks_region)

        for i in range(len(day_selected_routes_df)):
            route = day_selected_routes_df['WoolWorths routes'][i]
            all_routes.append({
                'region': region,
                'routes': route
            })

    all_routes = pd.DataFrame(all_routes)
    all_routes.to_csv(final_file_name, index=False)

    return route, final_file_name


def load_all_data():
    df1 = pd.read_csv('../0_Fixed Data - Initial Setup data/WoolworthsLocations.csv')
    AllStores = df1['Store']

    duration_df = pd.read_csv('../0_Fixed Data - Initial Setup data/WoolworthsDurations.csv')
    duration_df.rename(columns={'Unnamed: 0': 'Origin'}, inplace=True)
    duration_df_index = duration_df.set_index('Origin')
    df3 = duration_df.drop(columns=['Origin'])
    duration_matrix = df3.to_numpy()

    #traffic_duration_df = durations_traffic_based(duration_df)
    # duration_df_index = traffic_duration_df.set_index('Origin')
    # df3 = traffic_duration_df.drop(columns=['Origin'])
    # duration_matrix = df3.to_numpy()

    region_file_path = '../Region/All_info.csv'
    all_region_info = pd.read_csv(region_file_path)

    regions = [0, 1, 2, 3, 4, 5, 6, 7]
    num_trucks_per_cluster = [5, 2, 3, 4, 3, 2, 3, 2]

    return AllStores, duration_df_index, all_region_info, regions, num_trucks_per_cluster


if __name__ == '__main__':
    route, final_file_name = main()


    #df = df.sort_values(by='region')
    #df.to_csv('test_simulation.csv', index=False)
    #df.to_csv('weekday_simulation_data.csv', index=False)
    #df.to_csv('simulation_saturday_data.csv', index=False)
