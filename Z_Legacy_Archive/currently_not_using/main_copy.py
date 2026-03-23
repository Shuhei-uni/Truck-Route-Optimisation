from traffic_routes_module import *
import matplotlib.pyplot as plt
import seaborn as sns

from LP_Simulation_Select_Route_Region import *

# import LP functions as well
# hardcode the regions, easier to use
central_auckland_stores = [
    'FreshChoice Epsom',
    'FreshChoice Glen Eden',
    'Woolworths Auckland City',
    'Woolworths Auckland Victoria Street West',
    'Woolworths Grey Lynn',
    'Woolworths Pt Chevalier',
    'Woolworths Newmarket',
    'Woolworths Greenlane',
    'Woolworths Ponsonby',
    'Woolworths Mt Eden',
    'Woolworths Mt Wellington',
    'Woolworths St Lukes'
]

south_south_auckland_stores = [
    'Woolworths Roselands',
    'Woolworths Takanini',
    'Woolworths Waiata Shores',
    'FreshChoice Papakura',
    'Woolworths Papakura'
]

east_auckland_stores = [
    'Woolworths Pakuranga',
    'Woolworths Botany Downs',
    'Woolworths Meadowbank',
    'Woolworths St Johns',
    'Woolworths Meadowlands',
    'FreshChoice Half Moon Bay',
    'Woolworths Howick',
    'Woolworths Highland Park'
]

south_auckland_stores = [
    'Woolworths Mangere East',
    'Woolworths Airport',
    'FreshChoice Flat Bush',
    'FreshChoice Otahuhu',
    'Woolworths Manukau Mall',
    'Woolworths Mangere Mall',
    'FreshChoice Mangere Bridge',
    'Woolworths Onehunga',
    'Woolworths Manukau',
    'Woolworths Manurewa',
    'Woolworths Papatoetoe'
]

west_auckland_stores = [
    'Woolworths Henderson',
    'FreshChoice Palomino',
    'Woolworths Hobsonville',
    'FreshChoice Ranui',
    'Woolworths Te Atatu North',
    'Woolworths Lincoln Road',
    'Woolworths Te Atatu South',
    'Woolworths Northwest',
    'Woolworths Westgate'
]

west_central_auckland_stores = [
    'SuperValue Avondale',
    'Woolworths Blockhouse Bay',
    'Woolworths Three Kings',
    'FreshChoice Titirangi',
    'Woolworths Lynnmall',
    'Woolworths Mt Roskill'
]

north_auckland_stores = [
    'Woolworths Milford',
    'Woolworths Hauraki Corner',
    'Woolworths Northcote',
    'Woolworths Takapuna',
    'Woolworths Birkenhead',
    'Metro Halsey Street',
    'Metro Albert Street',
    'Woolworths Glenfield',
    'Metro Herne Bay'
]

north_north_auckland_stores = [
    'Woolworths Mairangi Bay',
    'Woolworths Browns Bay',
    'Woolworths Greville Road',
    'Woolworths Sunnynook'
]

regions = [0, 1, 2, 3, 4, 5, 6, 7]
num_trucks_per_cluster = [5, 2, 3, 4, 3, 2, 3, 2]


# load the data
<<<<<<< HEAD:main_copy.py
#data = pd.read_csv('0_Fixed Data - Initial Setup data/WoolworthsDemand2024.csv')
durations_df = pd.read_csv('0_Fixed Data - Initial Setup data/WoolworthsDurations.csv')
#simulated_demands = pd.read_csv('0_Non-Fixed Data - Simulation Data/simulated_store_demand.csv')
#demands_data = pd.read_csv('0_Fixed Data - Initial Setup data/rounded_weekends_75th_percentile.csv')
#name = data['Store']
#names = []
#percentile_demand = demands_data['75th Percentile Weekends']
#for i in range(64):
    #names.append(name[i])
#names.append('Distribution Centre Auckland')
=======
data = pd.read_csv('../0_Fixed Data - Initial Setup data/WoolworthsDemand2024.csv')
durations_df = pd.read_csv('../0_Fixed Data - Initial Setup data/WoolworthsDurations.csv')
simulated_demands = pd.read_csv('0_Non-Fixed Data - Simulation Data/simulated_store_demand.csv')
demands_data = pd.read_csv('../0_Fixed Data - Initial Setup data/rounded_weekends_75th_percentile.csv')
name = data['Store']
names = []
percentile_demand = demands_data['75th Percentile Weekends']
for i in range(64):
    names.append(name[i])
names.append('Distribution Centre Auckland')
>>>>>>> a9821c03108595a4952ea4f25da2f9ffff5be87f:currently_not_using/main_copy.py
# cen_routes = all_routes(names, percentile_demand, central_auckland_stores, durations_df)
current_duration = durations_traffic_based(durations_df)
print(current_duration)
'''
def main():
    for i in range(100):
        # simulate 100 times(normally distributed demands)
        costs = np.zeros(100)
        current_weekday_demands = np.zeros(64)
        current_weekend_demands = np.zeros(64)
        for j in range(64):
            # get the demand data for this current simulation
            weekday_demands = simulated_demands['Weekday Simulated Demand']
            weekend_demands = simulated_demands['Weekend Simulated Demand']
            current_weekday_demands[j] = weekday_demands[j + i]
            current_weekend_demands[j] = weekend_demands[j + i]
        # generate the routes for rigions
        current_duration = durations_traffic_based(durations_df)
        # random duration matrix that is caused by traffic factor(gaussian distribution)

        # check region routes, if the fixed/premade routes work
        # if not, generate new routes

        for routes in pre_made_routes_df:
            # Loop through all of the stores wihtin the route, is it greater than 20 or less than 20.
            # If it is greater than 20, then we need to generate new routes.


        # generate routes for each region, weekdays
        cen_weekday_routes = all_routes(names, current_weekday_demands, central_auckland_stores, current_duration)
        sou_south_weekday_routes = all_routes(names, current_weekday_demands, south_south_auckland_stores, current_duration)
        east_weekday_routes = all_routes(names, current_weekday_demands, east_auckland_stores, current_duration)
        south_weekday_routes = all_routes(names, current_weekday_demands, south_auckland_stores, current_duration)
        west_weekday_routes = all_routes(names, current_weekday_demands, west_auckland_stores, current_duration)
        westcen_weekday_routes = all_routes(names, current_weekday_demands, west_central_auckland_stores, current_duration)
        north_weekday_routes = all_routes(names, current_weekday_demands, north_auckland_stores, current_duration)
        nor_north_weekday_routes = all_routes(names, current_weekday_demands, north_north_auckland_stores, current_duration)

        # generate routes for each regions, weekends
        cen_weekend_routes = all_routes(names, current_weekend_demands, central_auckland_stores, current_duration, weekend=True)
        sou_south_weekend_routes = all_routes(names, current_weekend_demands, south_south_auckland_stores, current_duration, weekend=True)
        east_weekend_routes = all_routes(names, current_weekend_demands, east_auckland_stores, current_duration, weekend=True)
        south_weekend_routes = all_routes(names, current_weekend_demands, south_auckland_stores, current_duration, weekend=True)
        west_weekend_routes = all_routes(names, current_weekend_demands, west_auckland_stores, current_duration, weekend=True)
        westcen_weekend_routes = all_routes(names, current_weekend_demands, west_central_auckland_stores, current_duration, weekend=True)
        north_weekend_routes = all_routes(names, current_weekend_demands, north_auckland_stores, current_duration, weekend=True)
        nor_north_weekend_routes = all_routes(names, current_weekend_demands, north_north_auckland_stores, current_duration, weekend=True)

        #all_routes_weekday = []

        # LPs to select routes for regions
        for region_routes in all_route:

            #will return the routes and the duration per route
            routes_region = LP_Simulation_Select_Route_Region(region_routes, region_num,num_trucks_per_cluster)

            #calculate the cost per region,
            cost_per_region = calculate_cost(routes_region)

            all_routes.append({
                'region': region,
                'routes': routes_region,
                'duration': duration,
                'cost': cost_per_region
            })



        all_routes_df = pd.DataFrame(all_routes)


        # # calculate costs
        # costs[i] =
        # # visualize costs against total demands this day maybe.
        # plot = sns.boxplot()
        # plot.title("")
        # plot.xlabel('')
        # plot.ylabel('')
        # plt.show(plot)
'''