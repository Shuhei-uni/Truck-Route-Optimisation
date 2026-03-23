import pandas as pd
import numpy as np
from LP_Simulation_Select_Route_Region import *
from Routes.route_generation_per_region import *
from Routes.sort_algo import *

def main():

    """
    Change this to get weekday or saturday data, this is the only change you need to make!!
    """
    weekday = True

    if weekday == True:
        simulation_demand_data = pd.read_csv('0_Non-FixedData-SimulationData/weekday_simulation_demand.csv')
        final_file_name = 'currently_not_using/weekday_simulation_data.csv'
        final_routes_file_name = 'currently_not_using/weekday_simulation_routes.csv'
        number_trucks = [5, 2, 3, 4, 3, 2, 3, 2]

    else:
        simulation_demand_data = pd.read_csv('0_Non-FixedData-SimulationData/saturday_simulation_demand.csv')
        final_file_name = 'currently_not_using/saturday_simulation_data.csv'
        final_routes_file_name = 'currently_not_using/saturday_simulation_routes.csv'
        number_trucks = [5, 2, 3, 4, 3, 2, 3, 2]
    ###################################################################

    data = []
    route = []

    (AllStores, traffic_duration_df, all_region_info,
     regions) = load_all_data()


    for day in simulation_demand_data.columns:
        if day == 'Store':
            continue

        Demand = pd.Series(simulation_demand_data[day].to_numpy(), index=AllStores[:64])
        last_row = pd.Series([0], index=['Distribution Centre Auckland'])
        Demand = pd.concat([Demand, last_row])

        for region in regions:

            number_trucks_region = number_trucks[region]

            regional_data = all_region_info[all_region_info['Cluster'] == region]
            regional_stores = regional_data['Store']


            day_routes_df = route_per_region(region, regional_stores, Demand, traffic_duration_df)
            day_all_routes_df = pd.DataFrame(day_routes_df)

            temp_file_saved = 'tempfiles_ignore_pls/testing_main.csv'
            day_all_routes_df.to_csv(temp_file_saved, index=False)
            day_all_routes_df = remove_duplicate_rows(temp_file_saved, Demand, traffic_duration_df)
            day_all_routes_df.to_csv(temp_file_saved, index=False)
            day_selected_routes_df = selecting_routes_per_region(temp_file_saved, region, number_trucks_region)

            total_cost = day_selected_routes_df['total_cost'][0]
            total_ww_cost = day_selected_routes_df['Cost of WW trucks'][0]

            WW_selected_routes_df = day_selected_routes_df['WoolWorths routes']
            Outsourced_routes_df = day_selected_routes_df['Outsourced routes']
            max_length = max(len(WW_selected_routes_df), len(Outsourced_routes_df))

            data.append({
                'region': region,
                'day': day,
                'total_trucks': number_trucks_region,
                'total_routes': day_selected_routes_df['Number of Routes'][0],
                'total_overworked': day_selected_routes_df['Number of overworked'][0],
                'total_double_shift': day_selected_routes_df['Number of double shift'][0],
                'total_cost': total_cost,
                'cost_overworked': day_selected_routes_df['Money Spent on overworked shift'][0],
                'total_ww_cost': total_ww_cost
            })

            for i in range(len(day_selected_routes_df)):
                just_WW_route = day_selected_routes_df['WoolWorths routes'][i]
                just_OS_route = day_selected_routes_df['Outsourced routes'][i]
                route.append({
                    'region': region,
                    'day': day,
                    'Woolworths routes': just_WW_route,
                    'Outsourced routes': just_OS_route
                })

    return data, route, final_file_name, final_routes_file_name


def load_all_data():
    df1 = pd.read_csv('0_Fixed Data - Initial Setup data/WoolworthsLocations.csv')
    AllStores = df1['Store']

    duration_df = pd.read_csv('Durations_traffic_based.csv')
    duration_df.rename(columns={'Unnamed: 0': 'Origin'}, inplace=True)
    duration_df_index = duration_df.set_index('Origin')
    df3 = duration_df.drop(columns=['Origin'])
    duration_matrix = df3.to_numpy()

    region_file_path = 'Region/All_info.csv'
    all_region_info = pd.read_csv(region_file_path)

    regions = [0, 1, 2, 3, 4, 5, 6, 7]


    return AllStores, duration_df_index, all_region_info, regions


if __name__ == '__main__':
    df, route, final_file_name, final_routes_file_name = main()


    df = pd.DataFrame(df)
    route = pd.DataFrame(route)
    #df = df.sort_values(by='region')
    #df.to_csv('test_simulation.csv', index=False)
    #df.to_csv('weekday_simulation_data.csv', index=False)
    #df.to_csv('simulation_saturday_data.csv', index=False)
    df.to_csv(final_file_name, index=False)
    route.to_csv(final_routes_file_name, index=False)