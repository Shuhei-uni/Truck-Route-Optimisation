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
        simulation_demand_data = pd.read_csv('0_Non-FixedData-SimulationData/weekday_simulation_demand.csv')
        final_file_name = '~~~FINAL DATA STORED WITHIN/weekday_simulation_data.csv'
        final_routes_file_name = '~~~FINAL DATA STORED WITHIN/weekday_simulation_routes.csv'
    else:
        simulation_demand_data = pd.read_csv('0_Non-FixedData-SimulationData/saturday_simulation_demand.csv')
        final_file_name = '~~~FINAL DATA STORED WITHIN/saturday_simulation_data.csv'
        final_routes_file_name = '~~~FINAL DATA STORED WITHIN/saturday_simulation_routes.csv'
    ###################################################################

    data = []
    route = []

    (AllStores, traffic_duration_df, all_region_info,
     regions, num_trucks_per_cluster) = load_all_data()


    for day in simulation_demand_data.columns:
        if day == 'Store':
            continue

        Demand = pd.Series(simulation_demand_data[day].to_numpy(), index=AllStores[:64])
        last_row = pd.Series([0], index=['Distribution Centre Auckland'])
        Demand = pd.concat([Demand, last_row])

        # Bug 3 fix: Alternate between shift 1 (8am, peak-hour) and shift 2 (2pm, afternoon)
        # across simulation days to capture both traffic profiles.
        day_index = list(simulation_demand_data.columns).index(day) - 1  # subtract 1 for 'Store' col
        is_shift2 = (day_index % 2 == 1)  # even days = shift1, odd days = shift2
        is_weekend = not weekday  # weekend flag from the global toggle

        for region in regions:
            number_trucks_region = num_trucks_per_cluster[region]

            regional_data = all_region_info[all_region_info['Cluster'] == region]
            regional_stores = regional_data['Store']


            day_routes_df = route_per_region(region, regional_stores, Demand, traffic_duration_df, shift2=is_shift2, weekend=is_weekend)
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
                'total_cost': total_cost,
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
    num_trucks_per_cluster = [5, 2, 3, 4, 3, 2, 3, 2]

    return AllStores, duration_df_index, all_region_info, regions, num_trucks_per_cluster


if __name__ == '__main__':
    df, route, final_file_name, final_routes_file_name = main()

    df = pd.DataFrame(df)
    route = pd.DataFrame(route)

    df.to_csv(final_file_name, index=False)
    route.to_csv(final_routes_file_name, index=False)

    # -----------------------------------------------------------------
    # Bug 6 fix: Simulation cost aggregation and summary report.
    # Aggregate per-day total cost across all regions, then summarise.
    # -----------------------------------------------------------------
    daily_costs = df.groupby('day')['total_cost'].sum().reset_index()
    daily_costs.columns = ['day', 'daily_total_cost']

    daily_ww_costs = df.groupby('day')['total_ww_cost'].sum().reset_index()
    daily_costs['daily_ww_cost'] = daily_ww_costs['total_ww_cost']
    daily_costs['daily_mainfreight_cost'] = daily_costs['daily_total_cost'] - daily_costs['daily_ww_cost']

    n_sim_days = len(daily_costs)
    mean_daily = daily_costs['daily_total_cost'].mean()
    std_daily = daily_costs['daily_total_cost'].std()
    min_daily = daily_costs['daily_total_cost'].min()
    max_daily = daily_costs['daily_total_cost'].max()
    p95_daily = daily_costs['daily_total_cost'].quantile(0.95)

    # Scale to annual: 260 weekdays or 52 Saturdays depending on mode
    # The weekday flag is re-read here from final_file_name path as a proxy
    scale_days = 260 if 'weekday' in final_file_name else 52
    annual_mean = mean_daily * scale_days
    # 95% CI for the mean: mean ± 1.96 * std / sqrt(n)
    ci_95 = 1.96 * std_daily / (n_sim_days ** 0.5) * scale_days

    mainfreight_days = (daily_costs['daily_mainfreight_cost'] > 0).sum()
    mainfreight_pct = mainfreight_days / n_sim_days * 100

    summary = {
        'metric': [
            'Simulated days',
            'Mean daily cost ($)',
            'Std dev daily cost ($)',
            'Min daily cost ($)',
            'Max daily cost ($)',
            '95th pct daily cost ($)',
            f'Expected annual cost ({scale_days} days) ($)',
            '95% CI annual cost (+/-) ($)',
            '% days Mainfreight needed',
        ],
        'value': [
            n_sim_days,
            round(mean_daily, 2),
            round(std_daily, 2),
            round(min_daily, 2),
            round(max_daily, 2),
            round(p95_daily, 2),
            round(annual_mean, 2),
            round(ci_95, 2),
            round(mainfreight_pct, 1),
        ]
    }

    summary_df = pd.DataFrame(summary)
    summary_file = final_file_name.replace('_simulation_data.csv', '_simulation_summary.csv')
    summary_df.to_csv(summary_file, index=False)
    daily_costs.to_csv(final_file_name.replace('_simulation_data.csv', '_daily_costs.csv'), index=False)

    print('\n========== SIMULATION SUMMARY ==========')
    print(summary_df.to_string(index=False))
    print('========================================\n')
    print(f'Summary saved to: {summary_file}')