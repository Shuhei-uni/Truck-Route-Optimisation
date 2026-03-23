"""

Precondition:
    A set region and the number of trucks per region are given.


-----------------------------------------------------------

Generate/Read simulation of the demands per store.
Generate/Read simulation of the traffic duration and apply them to the duration matrix.

------------------------------------------------------------
Read the fixed routes, that are pre-made with the mean demands.

Does the current routes that are already made work for the given region?
If so don't regenerate the routes, just use the existing routes.

-------------------------------------------------------
For the regions where the fixed routes doesn't work

Loop through region by region:
for region_stores in region_stores_df:


    Route---------------------------------------------------------

    # Generate route per region.

    routing dataFrame will consist the routes, total_duration_per_route, total_demand_per_route.
    Format it exactly the same as last csv.

    route_df = generate_route_per_region(region_stores, simulation_demand, simulation_duration)


    LP----------------------------------------------------------------

    Objective: Minimise cost within the region
    route_duration * cost_per_hour + excess_duration * excess_cost_per_hour
    + outsource_cost_per_hour * outsource_duration

    Constraints:
    1. Each store receives exactly one delivery per day.
    2. A route can either be completed by our own trucks or outsourced, but not both.
    3. Number of trucks allocated to the region must be used.
            e.g. if 3 trucks, minimum of 3 routes need to be selected
    4. All other constraints that was used in the previous LPs.

    # Decide the routes to be selected.
    selected_routes_df will consist of the route, total_duration, total_demand.


    selected_routes_df = selecting_routes_per_region(route_df, num_trucks)


    Calculation and Finalising-------------------------------------------------------

    # Given the selected routes, find the route with the lowest duration
    # and assign it as the main freight route.

    main_freight_route = find_minimal_duration(total_duration)

    # Calculate total cost for the region.
    total_cost_region = calculate_total_cost(selected_routes_df, main_freight_route)


    woolworths_routing_df.append({
        'region': region_number,
        'selected_routes': selected_routes_df,
        'main_freight_route': main_freight_route,
        'total_cost': total_cost_region
    })

    total cost on that day
    number of mainfreight trucks used
    number of overworked workers

    total cost per region.

"""