"""
Global_LP.py
============
Phase 1b: Single global LP across all Auckland routes.

Replaces the old per-region LP loop. All 569 candidate routes are loaded into
one DataFrame and solved in a single PuLP problem. The fleet constraint is a
global cap (total_fleet_size * 2 shift-slots) rather than per-region quotas,
allowing trucks to be dynamically allocated where demand is highest.

Usage:
    python Global_LP.py                    # reads params.json or default args
    python Global_LP.py --fleet 20         # override fleet size command line

Outputs:
    Fixed Routes - Final/master_schedule.csv
"""

import ast
import math
import argparse
import pandas as pd
import json
import os
from pulp import (
    LpProblem, LpMinimize, LpVariable, lpSum,
    LpBinary, LpStatus, value, PULP_CBC_CMD
)

def solve_global_lp(
    total_fleet_size: int = 24, 
    routes_csv: str = None,
    truck_cost: float = 75_000,
    mf_cost: float = 2300,
    ot_rate: float = 325,
) -> pd.DataFrame:
    """
    Solve the global set-partitioning LP and return the master schedule.
    """
    if routes_csv is None:
        routes_csv = 'Routes/routes_per_region_filtered.csv'

    routes_df = pd.read_csv(routes_csv)
    routes_df = routes_df.reset_index(drop=True)

    # Pre-parse route lists once
    routes_df['route_list'] = routes_df['routes'].apply(ast.literal_eval)
    n = len(routes_df)
    print(f"  Loaded {n} candidate routes across {routes_df['region'].nunique()} regions.")

    # Sub-functions for costs using dynamic rates
    ww_cost_per_sec = 250 / 3600
    ot_cost_per_sec = ot_rate / 3600
    shift_len = 14400

    def mainfreight_cost(duration_seconds: float) -> float:
        return math.ceil(duration_seconds / shift_len) * mf_cost

    def ww_route_cost(duration_seconds: float) -> float:
        in_shift  = ww_cost_per_sec * min(duration_seconds, shift_len)
        overtime  = ot_cost_per_sec * max(0, duration_seconds - shift_len)
        return in_shift + overtime

    # Decision variables
    prob = LpProblem("Woolworths_Global_Routing", LpMinimize)
    WW  = LpVariable.dicts("WW",         range(n), 0, 1, LpBinary)
    MF  = LpVariable.dicts("Mainfreight", range(n), 0, 1, LpBinary)

    # Objective
    daily_route_cost = lpSum(
        WW[i] * ww_route_cost(routes_df['total_duration'].iloc[i])
        + MF[i] * mainfreight_cost(routes_df['total_duration'].iloc[i])
        for i in range(n)
    )
    annual_fleet_maintenance = total_fleet_size * truck_cost / 365
    prob += daily_route_cost + annual_fleet_maintenance

    # Constraint 1: Every store covered exactly once
    all_stores = set()
    for route_list in routes_df['route_list']:
        all_stores.update(route_list)
    all_stores.discard('Distribution Centre Auckland')

    for store in all_stores:
        serving = [
            i for i in range(n)
            if store in routes_df['route_list'].iloc[i]
        ]
        if serving:
            prob += lpSum(WW[i] + MF[i] for i in serving) == 1, f"Cover_{store}"

    # Constraint 2: A route can't be both WW and Mainfreight
    for i in range(n):
        prob += WW[i] + MF[i] <= 1, f"Exclusive_{i}"

    # Constraint 3: Global WW shift cap
    prob += lpSum(WW[i] for i in range(n)) <= total_fleet_size * 2, "Fleet_Cap"

    # Solve
    print(f"  Solving LP: fleet={total_fleet_size}, truck_cost=${truck_cost}, MF=${mf_cost}, OT=${ot_rate}/hr ...")
    prob.solve(PULP_CBC_CMD(msg=False))

    status = LpStatus[prob.status]
    print(f"  LP Status: {status}")
    print(f"  Objective (daily cost + maintenance): ${value(prob.objective):,.2f}")

    # Extract results
    selected = []
    for i in range(n):
        ww_val = WW[i].varValue or 0
        mf_val = MF[i].varValue or 0
        if ww_val > 0.5 or mf_val > 0.5:
            assigned = 'WW' if ww_val > 0.5 else 'Mainfreight'
            selected.append({
                'route':       routes_df['routes'].iloc[i],
                'duration':    routes_df['total_duration'].iloc[i],
                'demand':      routes_df['total_demand'].iloc[i],
                'region':      routes_df['region'].iloc[i],
                'assigned_to': assigned,
                'route_cost':  (
                    ww_route_cost(routes_df['total_duration'].iloc[i])
                    if assigned == 'WW'
                    else mainfreight_cost(routes_df['total_duration'].iloc[i])
                )
            })

    master_df = pd.DataFrame(selected)

    ww_count = (master_df['assigned_to'] == 'WW').sum()
    mf_count = (master_df['assigned_to'] == 'Mainfreight').sum()
    stores_covered = set()
    for row in master_df['route']:
        stores_covered.update(ast.literal_eval(row))
    stores_covered.discard('Distribution Centre Auckland')

    print(f"\n  --- Master Schedule Summary ---")
    print(f"  WW routes:           {ww_count}")
    print(f"  Mainfreight routes:  {mf_count}")
    print(f"  Stores covered:      {len(stores_covered)}/{len(all_stores)}")
    print(f"  Daily routing cost:  ${value(prob.objective) - annual_fleet_maintenance:,.2f}")
    print(f"  Fleet maintenance:   ${annual_fleet_maintenance:,.2f}/day")

    return master_df

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Woolworths Global LP Solver")
    parser.add_argument('--fleet', type=int, default=None, help='Override fleet size')
    args = parser.parse_args()

    # Load defaults from Interactive_Report/params.json if it exists
    fleet_sz = 24
    tk_cost = 75000
    mf_block = 2300
    ot_rate_hr = 325

    params_path = os.path.join('Interactive_Report', 'params.json')
    if os.path.exists(params_path):
        with open(params_path, 'r') as f:
            j = json.load(f)
            fleet_sz = j.get('fleetSize', fleet_sz)
            tk_cost = j.get('truckCost', tk_cost)
            mf_block = j.get('mfCost', mf_block)
            ot_rate_hr = j.get('otRate', ot_rate_hr)
            
    if args.fleet is not None:
        fleet_sz = args.fleet

    print(f"\n{'='*50}")
    print(f"  Global LP Engine")
    print(f"{'='*50}")

    master_df = solve_global_lp(
        total_fleet_size=fleet_sz,
        truck_cost=tk_cost,
        mf_cost=mf_block,
        ot_rate=ot_rate_hr
    )

    output_path = 'Fixed Routes - Final/master_schedule.csv'
    master_df.to_csv(output_path, index=False, quoting=1)
    print(f"\n  Master schedule saved to: {output_path}")
    print(f"{'='*50}\n")
