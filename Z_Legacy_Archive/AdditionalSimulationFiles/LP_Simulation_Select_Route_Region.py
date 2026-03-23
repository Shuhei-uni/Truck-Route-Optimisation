import pandas as pd
from pulp import LpProblem, LpMinimize, LpVariable, lpSum, LpBinary, LpStatus, value
import ast
import math
from pulp import PULP_CBC_CMD




def selecting_routes_per_region(file, region, num_trucks_per_region):
    routes_df = pd.read_csv(file)
    # Select the routes to be used for the region.
    # Extract the number of routes
    num_routes = len(routes_df)

    # Define the problem
    prob = LpProblem(f"Woolworths_Truck_Routing_Region_{region}", LpMinimize)

    # Route decision variables

    # Routes completed by WW trucks
    WW_routes = LpVariable.dicts("Route", range(num_routes), 0, 1, LpBinary)
    # Routes outsourced
    outsourced_routes = LpVariable.dicts("Outsource", range(num_routes), 0, 1, LpBinary)

    # Objective function: Minimize the total cost
    # Bug 2 fix: Mainfreight charges $2300 per 4-hour block (rounded up), not per second.
    def mainfreight_cost(duration_seconds):
        return math.ceil(duration_seconds / 14400) * 2300

    prob += lpSum([(WW_routes[i] * (250 / 3600 * min(routes_df['total_duration'].iloc[i], 14400)))
                   + (WW_routes[i] * (325 / 3600 * max(0, routes_df['total_duration'].iloc[i] - 14400)))
                   + (outsourced_routes[i] * mainfreight_cost(routes_df['total_duration'].iloc[i])) for i in range(num_routes)]) + (num_trucks_per_region * 75000/365)

    # Extract the unique stores from the routes, discarding distribution center, prep for Constraint 1
    stores = set()
    for route in routes_df['routes']:
        stores.update(ast.literal_eval(route))
    stores.discard('Distribution Centre Auckland')  # Remove the distribution center from the set

    # Constraint 1:
    # Bug 1 fix: Each store receives exactly one delivery per day from either a WW truck or an outsourced truck.
    for store in stores:
        prob += lpSum(
            [WW_routes[i] + outsourced_routes[i]
             for i in range(num_routes)
             if store in ast.literal_eval(routes_df['routes'].iloc[i])]
        ) == 1

    # Constraint 2:
    # A route can either be completed by our own trucks or outsourced, but not both (outsourcing doesn't change optimal sol)
    for i in range(num_routes):
        prob += WW_routes[i] + outsourced_routes[i] <= 1

    # Constraint 3:
    # Bug 4 fix: Use the actual truck count for this region, not a hardcoded 10.
    # When demand exceeds capacity, the LP will automatically spill to outsourced_routes (Mainfreight).
    prob += lpSum(WW_routes[i] for i in range(num_routes)) <= num_trucks_per_region

    # Solve the problem
    prob.solve(PULP_CBC_CMD(msg=False))

    # Output the status and the selected routes for the current region
    status = LpStatus[prob.status]
    WW_selected_routes = [i for i in range(num_routes) if WW_routes[i].varValue > 0]
    outsource_selected_routes = [i for i in range(num_routes) if outsourced_routes[i].varValue > 0]

    # Get the number of WW trucks that went over `14400` seconds
    WW_trucks_over_14400 = [routes_df['total_duration'].iloc[route] for route in WW_selected_routes if routes_df['total_duration'].iloc[route] > 14400]
    # Get the time spent over `14400` seconds
    cost_overworked = sum((time - 14400) for time in WW_trucks_over_14400) * 325 / 3600



    # Store the selected routes/duration/demands
    WW_selected_routes_df = [(routes_df['routes'].iloc[route]) for route in WW_selected_routes]
    WW_times = [(routes_df['total_duration'].iloc[route]) for route in WW_selected_routes]
    Outsourced_routes_df = [(routes_df['routes'].iloc[route]) for route in outsource_selected_routes]
    Outsourced_times = [(routes_df['total_duration'].iloc[route]) for route in outsource_selected_routes]

    total_demand = sum([(routes_df['total_demand'].iloc[route]) for route in WW_selected_routes] + [(routes_df['total_demand'].iloc[route]) for route in outsource_selected_routes])
    cost_outsourced_trucks = sum(Outsourced_times) * 2300 / 3600
    cost_WW_trucks = value(prob.objective) - cost_outsourced_trucks

    # Ensure all lists are of equal length before DataFrame creation
    max_length = max(len(WW_selected_routes_df), len(Outsourced_routes_df))

    # Padding with empty strings if needed
    WW_selected_routes_df.extend([""] * (max_length - len(WW_selected_routes_df)))
    WW_times.extend([""] * (max_length - len(WW_times)))
    Outsourced_routes_df.extend([""] * (max_length - len(Outsourced_routes_df)))
    Outsourced_times.extend([""] * (max_length - len(Outsourced_times)))


    number_selected_routes = 0
    for i in range(num_routes):
        if WW_routes[i].varValue > 0:
            number_selected_routes += 1
        if outsourced_routes[i].varValue > 0:
            number_selected_routes += 1

    double_shift = number_selected_routes - num_trucks_per_region
    if double_shift < 0:
        double_shift = 0

    # Creating the DataFrame
    selected_routes_df = pd.DataFrame({
        'region': [region] * max_length,
        'Number of Trucks': [num_trucks_per_region] * max_length,
        'Number of Routes': [number_selected_routes] * max_length,
        'WoolWorths routes': WW_selected_routes_df,
        'WoolWorths duration': [WW_times[i] for i in range(len(WW_times))],
        'Cost of WW trucks': cost_WW_trucks,
        'Number of overworked': len(WW_trucks_over_14400),
        'Number of double shift': [double_shift] * max_length,
        'Money Spent on overworked shift': cost_overworked,
        'Outsourced routes': Outsourced_routes_df,
        'Outsourced duration': Outsourced_times,
        'Cost of OS trucks': cost_outsourced_trucks,
        'total_demand_from_routes': total_demand,
        'total_cost': [value(prob.objective)] * max_length
    })

    # Print the total demand


    # selected_routes_df will consist of the route, total_duration per route, total_demand per route.
    #selected_routes_df.to_csv('../tempfiles_ignore_pls/tempfile_LP.csv', index=False)
    selected_routes_df.to_csv('tempfiles_ignore_pls/LP_solved_df.csv', index=False)

    return selected_routes_df
