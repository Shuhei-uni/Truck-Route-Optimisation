import pandas as pd
from pulp import LpProblem, LpMinimize, LpVariable, lpSum, LpBinary, LpStatus, value
import ast

# Load routes
all_region_routes_df = pd.read_csv('../Routes/routes_per_region_filtered.csv')

# Define the regions
regions = [0, 1, 2, 3, 4, 5, 6, 7]
num_trucks_per_cluster = [5, 2, 3, 4, 3, 2, 3, 2]
index = 0

# Initialize a list to collect results for all regions
all_selected_routes = []

# Iterate over each region
for region in regions:
    # Filter the routes for the current region
    routes_df = all_region_routes_df[all_region_routes_df['region'] == region]

    # Extract the number of routes
    num_routes = len(routes_df)

    # Define the problem
    prob = LpProblem(f"Woolworths_Truck_Routing_Region_{region}", LpMinimize)

    # Decision variables
    x = LpVariable.dicts("Route", range(num_routes), 0, 1, LpBinary)  # Route decision variable (whether it is chosen or not)
    y = LpVariable.dicts("Outsource", range(num_routes), 0, 1, LpBinary)  # Outsourcing decision variable
    p = LpVariable.dicts("Pallets", range(num_routes), 0, None)  # New decision variable for the number of pallets on each route

    # Objective function: Minimize the total cost
    prob += lpSum([(x[i] * (75000 / 365 + 250 / 3600 * min(routes_df['total_duration'].iloc[i], 14400) +
                           325 / 3600 * max(0, routes_df['total_duration'].iloc[i] - 14400))) +
                   (y[i] * 2300 / 3600 * routes_df['total_duration'].iloc[i]) for i in range(num_routes)])

    # Extract the unique stores from the routes, discarding distribution center, prep for Constraint 1
    stores = set()
    for route in routes_df['routes']:
        stores.update(ast.literal_eval(route))
    stores.discard('Distribution Centre Auckland')  # Remove the distribution center from the set

    # Constraint 1:
    # 1 delivery - Each store receives exactly one delivery per day
    for store in stores:
        prob += lpSum([x[i] for i in range(num_routes) if store in ast.literal_eval(routes_df['routes'].iloc[i])]) == 1

    # Constraint 2:
    # A route can either be completed by our own trucks or outsourced, but not both (outsourcing doesn't change optimal sol)
    for i in range(num_routes):
        prob += x[i] + y[i] <= 1

    # Constraint 3:
    # Truck capacity constraint: Ensure that each truck does not exceed its capacity of 20 pallets
    for i in range(num_routes):
        prob += p[i] <= 20 * x[i]

    # Constraint 4:
    for i in range(num_routes):
        prob += x[i] <= num_trucks_per_cluster[index]
    index += 1

    # Solve the problem
    prob.solve()

    # Output the status and the selected routes for the current region
    status = LpStatus[prob.status]
    selected_routes = [i for i in range(num_routes) if x[i].varValue > 0]

    print(f"Region {region} Status:", status)
    print(f"Region {region} Selected Routes:", selected_routes)
    print(f"Region {region} Total Cost:", value(prob.objective))

    # Store the selected routes/duration/demands
    selected_routes_str = [str(routes_df['routes'].iloc[route]) for route in selected_routes]
    times_str = [str(routes_df['total_duration'].iloc[route]) for route in selected_routes]

    selected_routes_df = pd.DataFrame({
        'region': region,
        'routes': selected_routes_str,
        'duration': times_str
    })

    # Append the current region's selected routes to the overall list
    all_selected_routes.append(selected_routes_df)

# Concatenate all selected routes into a single DataFrame
all_selected_routes_df = pd.concat(all_selected_routes, ignore_index=True)

# Save the combined results to a CSV file
output_file_path = "../Fixed Routes - Final/all_regions_routes_selected_weekdays.csv"
all_selected_routes_df.to_csv(output_file_path, index=False, quoting=1)

print("Total number of selected routes across all regions:", len(all_selected_routes_df))
