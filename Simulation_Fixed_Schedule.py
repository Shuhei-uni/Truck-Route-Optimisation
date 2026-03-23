"""
Simulation_Fixed_Schedule.py
============================
Phase 3: Fixed Master Schedule Simulation with Penalty Recourse.

Architecture: The LP runs ONCE (via Global_LP.py) to create a master schedule.
This simulation tests that fixed schedule against 100 days of stochastic demand
WITHOUT re-solving the LP each day — which is a fundamental design improvement.

Recourse logic:
  - Each day, re-sum actual simulated store demands for every WW route.
  - If total pallets <= 20: route runs normally.
  - If total pallets > 20: WW truck takes exactly 20 pallets.
    Overflow stores get a direct out-and-back Mainfreight trip from the depot,
    charged at $2300 per 4-hour block.

Usage:
    python Simulation_Fixed_Schedule.py                  # weekday
    python Simulation_Fixed_Schedule.py --weekend        # saturday
    python Simulation_Fixed_Schedule.py --fleet 20       # specific fleet size

Outputs:
    Fixed Routes - Final/weekday_simulation_summary.csv
    Fixed Routes - Final/weekday_daily_costs.csv
"""

import ast
import math
import argparse
import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
WW_COST_PER_SEC       = 250 / 3600
OVERTIME_COST_PER_SEC = 325 / 3600
SHIFT_DURATION_SEC    = 14400
MF_BLOCK_COST         = 2300
UNLOAD_TIME_PER_PALLET = 600   # 10 min/pallet in seconds
DEPOT_NAME            = 'Distribution Centre Auckland'
DEMAND_SCALAR         = 1.0


def mainfreight_block_cost(duration_seconds: float) -> float:
    """$2300 per 4-hour block, rounded up."""
    return math.ceil(max(duration_seconds, 1) / SHIFT_DURATION_SEC) * MF_BLOCK_COST


def ww_route_cost(duration_seconds: float) -> float:
    """Operating cost for one WW route (driving + overtime if any)."""
    in_shift = WW_COST_PER_SEC * min(duration_seconds, SHIFT_DURATION_SEC)
    overtime = OVERTIME_COST_PER_SEC * max(0, duration_seconds - SHIFT_DURATION_SEC)
    return in_shift + overtime


def load_data(weekday: bool = True, fleet_size: int = 24):
    """Load all required data for the simulation."""
    # Master schedule (WW routes only — MF routes already priced in LP)
    master_df = pd.read_csv('Fixed Routes - Final/master_schedule.csv')
    ww_routes = master_df[master_df['assigned_to'] == 'WW'].copy()
    ww_routes['route_list'] = ww_routes['route'].apply(ast.literal_eval)

    # Simulated demand CSV (stores x 100 days)
    if weekday:
        demand_csv = '0_Non-FixedData-SimulationData/weekday_simulation_demand.csv'
    else:
        demand_csv = '0_Non-FixedData-SimulationData/saturday_simulation_demand.csv'
    demand_df = pd.read_csv(demand_csv, index_col='Store')

    # Duration matrix for out-and-back Mainfreight trip distances
    durations_df = pd.read_csv('0_Fixed Data - Initial Setup data/WoolworthsDurations.csv',
                               index_col=0)

    return ww_routes, demand_df, durations_df, fleet_size


def simulate_day(ww_routes: pd.DataFrame,
                 day_demand: pd.Series,
                 durations_df: pd.DataFrame) -> dict:
    """
    Simulate a single day against the fixed master schedule.

    For each WW route:
    - If route total demand <= 20: standard WW cost.
    - If route total demand > 20: WW takes 20 pallets, overflow stores
      get a Mainfreight out-and-back trip from the depot.

    Returns a dict of cost components for this day.
    """
    total_ww_cost        = 0.0
    total_mf_cost        = 0.0
    total_overtime_cost  = 0.0
    mainfreight_trips     = 0
    overflow_events       = 0

    for _, route_row in ww_routes.iterrows():
        route_stores = [
            s for s in route_row['route_list']
            if s != DEPOT_NAME
        ]

        # Re-sum actual demand for stores on this route today
        actual_demand = sum(
            int(day_demand.get(store, 0) * DEMAND_SCALAR) for store in route_stores
        )

        if actual_demand <= 20:
            # Normal delivery — use pre-computed route duration
            route_dur = route_row['duration']
            cost = ww_route_cost(route_dur)
            total_ww_cost += cost
            if route_dur > SHIFT_DURATION_SEC:
                total_overtime_cost += OVERTIME_COST_PER_SEC * (route_dur - SHIFT_DURATION_SEC)
        else:
            # Overflow: WW truck delivers 20 pallets, remaining stores get Mainfreight
            overflow_events += 1

            # WW delivers to first stores until truck is full (greedy fill)
            pallets_loaded = 0
            overflow_stores = []
            for store in route_stores:
                store_demand = int(day_demand.get(store, 0) * DEMAND_SCALAR)
                if pallets_loaded + store_demand <= 20:
                    pallets_loaded += store_demand
                else:
                    overflow_stores.append(store)

            # WW route cost using base route duration (truck still runs the route)
            route_dur = route_row['duration']
            cost = ww_route_cost(route_dur)
            total_ww_cost += cost

            # Each overflow store gets a direct out-and-back Mainfreight trip
            for store in overflow_stores:
                mainfreight_trips += 1
                try:
                    depot_to_store = durations_df.loc[DEPOT_NAME, store]
                    store_to_depot = durations_df.loc[store, DEPOT_NAME]
                    mf_drive_time = depot_to_store + store_to_depot
                except KeyError:
                    mf_drive_time = SHIFT_DURATION_SEC  # fallback: 1 block

                store_demand_mf = int(day_demand.get(store, 0))
                mf_unload_time = store_demand_mf * UNLOAD_TIME_PER_PALLET
                mf_total_time = mf_drive_time + mf_unload_time

                mf_trip_cost = mainfreight_block_cost(mf_total_time)
                total_mf_cost += mf_trip_cost

    total_cost = total_ww_cost + total_mf_cost

    return {
        'total_cost':       total_cost,
        'ww_cost':          total_ww_cost,
        'mf_cost':          total_mf_cost,
        'overtime_cost':    total_overtime_cost,
        'overflow_events':  overflow_events,
        'mf_trips':         mainfreight_trips,
    }


def run_simulation(weekday: bool = True, fleet_size: int = 24) -> tuple:
    """Run the full simulation and return (daily_costs_df, summary_df)."""
    ww_routes, demand_df, durations_df, _ = load_data(weekday, fleet_size)
    sim_days = [c for c in demand_df.columns]

    print(f"\n  Simulating {len(sim_days)} days against "
          f"{len(ww_routes)} fixed WW routes...")

    daily_records = []
    for day in sim_days:
        day_demand = demand_df[day]
        result = simulate_day(ww_routes, day_demand, durations_df)
        result['day'] = day
        daily_records.append(result)

    daily_df = pd.DataFrame(daily_records)

    # ------------------------------------------------------------------
    # Aggregation summary (same structure as Bug 6 fix)
    # ------------------------------------------------------------------
    scale_days = 260 if weekday else 52
    n = len(daily_df)

    mean_daily   = daily_df['total_cost'].mean()
    std_daily    = daily_df['total_cost'].std()
    min_daily    = daily_df['total_cost'].min()
    max_daily    = daily_df['total_cost'].max()
    p95_daily    = daily_df['total_cost'].quantile(0.95)
    annual_mean  = mean_daily * scale_days
    ci_95        = 1.96 * std_daily / (n ** 0.5) * scale_days
    mf_days_pct  = (daily_df['mf_cost'] > 0).mean() * 100
    mean_mf_trips= daily_df['mf_trips'].mean()
    mean_overflow= daily_df['overflow_events'].mean()

    summary = pd.DataFrame({
        'metric': [
            'Simulated days',
            'Mean daily cost ($)',
            'Std dev daily cost ($)',
            'Min daily cost ($)',
            'Max daily cost ($)',
            '95th pct daily cost ($)',
            f'Expected annual cost ({scale_days} days) ($)',
            '95% CI annual cost (+/-) ($)',
            '% days Mainfreight overflow triggered',
            'Mean Mainfreight trips per day',
            'Mean overflow events per day',
        ],
        'value': [
            n,
            round(mean_daily, 2),
            round(std_daily, 2),
            round(min_daily, 2),
            round(max_daily, 2),
            round(p95_daily, 2),
            round(annual_mean, 2),
            round(ci_95, 2),
            round(mf_days_pct, 1),
            round(mean_mf_trips, 2),
            round(mean_overflow, 2),
        ]
    })

    print('\n  ========== SIMULATION SUMMARY ==========')
    print(summary.to_string(index=False))
    print('  =========================================\n')

    return daily_df, summary, annual_mean


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Woolworths Fixed Schedule Simulation')
    parser.add_argument('--weekend', action='store_true',
                        help='Simulate Saturday demand instead of weekday')
    parser.add_argument('--fleet', type=int, default=24,
                        help='Fleet size used to generate master schedule (default: 24)')
    args = parser.parse_args()

    weekday = not args.weekend
    day_label = 'saturday' if not weekday else 'weekday'

    import os
    import json
    
    params_path = os.path.join('Interactive_Report', 'params.json')
    if os.path.exists(params_path):
        with open(params_path, 'r') as f:
            j = json.load(f)
            if args.fleet == 24:
                args.fleet = j.get('fleetSize', args.fleet)
            
            MF_BLOCK_COST = j.get('mfCost', MF_BLOCK_COST)
            OVERTIME_COST_PER_SEC = j.get('otRate', 325) / 3600
            DEMAND_SCALAR = j.get('demandMean', 15) / 15.0

    # Run the LP first if master schedule doesn't exist
    if not os.path.exists('Fixed Routes - Final/master_schedule.csv'):
        print("  Master schedule not found — running Global_LP.py first...")
        from Global_LP import solve_global_lp
        master = solve_global_lp(total_fleet_size=args.fleet)
        master.to_csv('Fixed Routes - Final/master_schedule.csv', index=False, quoting=1)

    daily_df, summary_df, annual_cost = run_simulation(
        weekday=weekday, fleet_size=args.fleet
    )

    # Save outputs
    summary_path = f'Fixed Routes - Final/{day_label}_simulation_summary.csv'
    daily_path   = f'Fixed Routes - Final/{day_label}_daily_costs.csv'
    summary_df.to_csv(summary_path, index=False)
    daily_df.to_csv(daily_path, index=False)

    print(f'  Summary saved to: {summary_path}')
    print(f'  Daily costs saved to: {daily_path}')
