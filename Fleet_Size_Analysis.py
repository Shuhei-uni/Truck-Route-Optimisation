"""
Fleet_Size_Analysis.py
======================
Phase 4: Fleet Size Sweep — the core business recommendation tool.

Loops over fleet sizes from 10 to 24 trucks, runs the global LP and fixed
schedule simulation for each, then computes:

    Total Annual Cost = (fleet_size * $75,000 maintenance) + annualised routing cost

The fleet size with the minimum total annual cost is the mathematically
supported recommendation to management.

Usage:
    python Fleet_Size_Analysis.py
    python Fleet_Size_Analysis.py --min_fleet 12 --max_fleet 24  # custom range
    python Fleet_Size_Analysis.py --weekend

Outputs:
    Fixed Routes - Final/fleet_size_results.csv
    Fixed Routes - Final/fleet_size_analysis.png
"""

import argparse
import os
import math
import pandas as pd
import matplotlib
matplotlib.use('Agg')   # non-interactive backend (no display required)
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

from Global_LP import solve_global_lp
from Simulation_Fixed_Schedule import run_simulation

ANNUAL_TRUCK_COST = 75_000
SCALE_WEEKDAY     = 260
SCALE_WEEKEND     = 52


def analyse_fleet_sizes(min_fleet: int = 10,
                        max_fleet: int = 24,
                        weekday: bool = True) -> pd.DataFrame:
    """
    For each fleet size in [min_fleet, max_fleet], solve the LP, run the
    simulation, and compute the total annual cost.

    Returns a DataFrame with one row per fleet size.
    """
    scale = SCALE_WEEKDAY if weekday else SCALE_WEEKEND
    day_label = 'weekday' if weekday else 'saturday'
    results = []

    print(f"\n{'='*60}")
    print(f"  Fleet Size Analysis  |  Range: {min_fleet}–{max_fleet} trucks")
    print(f"  Day type: {'Weekday' if weekday else 'Saturday'}")
    print(f"{'='*60}")

    for fleet_size in range(min_fleet, max_fleet + 1):
        print(f"\n  --- Fleet size: {fleet_size} ---")

        # Step 1: Solve LP for this fleet size
        master_df = solve_global_lp(total_fleet_size=fleet_size)

        # Save master schedule temporarily
        tmp_path = 'Fixed Routes - Final/master_schedule.csv'
        master_df.to_csv(tmp_path, index=False, quoting=1)

        # Step 2: Run fixed schedule simulation
        daily_df, summary_df, annual_routing_cost = run_simulation(
            weekday=weekday, fleet_size=fleet_size
        )

        # Step 3: Total annual cost
        annual_maintenance  = fleet_size * ANNUAL_TRUCK_COST
        total_annual_cost   = annual_maintenance + annual_routing_cost

        # Pull summary stats
        summary_dict = dict(zip(summary_df['metric'], summary_df['value']))
        mf_pct = summary_dict.get('% days Mainfreight overflow triggered', float('nan'))
        mean_daily_cost = summary_dict.get('Mean daily cost ($)', float('nan'))
        ci_95 = summary_dict.get('95% CI annual cost (+/-) ($)', float('nan'))

        # Count how many routes go to Mainfreight in the LP solution
        mf_routes_in_lp = (master_df['assigned_to'] == 'Mainfreight').sum()

        results.append({
            'fleet_size':             fleet_size,
            'annual_maintenance ($)': annual_maintenance,
            'annual_routing_cost ($)':round(annual_routing_cost, 2),
            'total_annual_cost ($)':  round(total_annual_cost, 2),
            'ci_95_annual ($)':       round(ci_95, 2),
            'mean_daily_cost ($)':    round(mean_daily_cost, 2),
            'mf_days_pct (%)':        mf_pct,
            'mf_routes_in_lp':        mf_routes_in_lp,
        })

        print(f"  Total Annual Cost: ${total_annual_cost:,.0f}  "
              f"(maintenance ${annual_maintenance:,.0f} + routing ${annual_routing_cost:,.0f})")

    results_df = pd.DataFrame(results)

    # Identify optimal fleet size
    opt_idx  = results_df['total_annual_cost ($)'].idxmin()
    opt_size = results_df.loc[opt_idx, 'fleet_size']
    opt_cost = results_df.loc[opt_idx, 'total_annual_cost ($)']

    print(f"\n{'='*60}")
    print(f"  RECOMMENDATION: {opt_size} trucks")
    print(f"  Minimum total annual cost: ${opt_cost:,.0f}")
    print(f"{'='*60}\n")

    return results_df, opt_size


def plot_results(results_df: pd.DataFrame,
                 opt_size: int,
                 weekday: bool = True):
    """
    Plot total annual cost breakdown and Mainfreight usage vs fleet size.
    """
    day_label = 'weekday' if weekday else 'saturday'

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 9), sharex=True)
    fig.patch.set_facecolor('#1a1a2e')

    for ax in (ax1, ax2):
        ax.set_facecolor('#16213e')
        ax.tick_params(colors='white')
        ax.xaxis.label.set_color('white')
        ax.yaxis.label.set_color('white')
        ax.title.set_color('white')
        for spine in ax.spines.values():
            spine.set_edgecolor('#444466')

    x = results_df['fleet_size']

    # --- Top chart: cost breakdown ---
    ax1.fill_between(x,
                     results_df['annual_maintenance ($)'] / 1e6,
                     alpha=0.4, color='#e94560', label='Maintenance cost')
    ax1.fill_between(x,
                     results_df['annual_routing_cost ($)'] / 1e6,
                     alpha=0.4, color='#0f3460', label='Routing cost')
    ax1.plot(x,
             results_df['total_annual_cost ($)'] / 1e6,
             color='#e2e2e2', linewidth=2.5, marker='o', markersize=6,
             label='Total annual cost')

    # 95% CI band on total cost
    ci = results_df['ci_95_annual ($)'] / 1e6
    total = results_df['total_annual_cost ($)'] / 1e6
    ax1.fill_between(x, total - ci, total + ci,
                     alpha=0.2, color='#e2e2e2', label='95% CI')

    # Optimal vertical line
    ax1.axvline(opt_size, color='#f5a623', linewidth=2, linestyle='--',
                label=f'Optimal: {opt_size} trucks')

    ax1.yaxis.set_major_formatter(mticker.FormatStrFormatter('$%.1fM'))
    ax1.set_ylabel('Annual Cost', color='white')
    ax1.set_title('Total Annual Cost vs Fleet Size', fontsize=14, pad=12)
    ax1.legend(facecolor='#16213e', edgecolor='#444466', labelcolor='white',
               fontsize=9, loc='upper right')
    ax1.grid(axis='y', color='#444466', linestyle=':', alpha=0.6)

    # Annotation at optimal
    opt_row = results_df[results_df['fleet_size'] == opt_size].iloc[0]
    ax1.annotate(
        f"  ${opt_row['total_annual_cost ($)']/1e6:.2f}M",
        xy=(opt_size, opt_row['total_annual_cost ($)'] / 1e6),
        color='#f5a623', fontsize=10, fontweight='bold'
    )

    # --- Bottom chart: Mainfreight usage ---
    ax2.bar(x, results_df['mf_days_pct (%)'],
            color='#e94560', alpha=0.75, label='% days overflow triggered')
    ax2.bar(x, results_df['mf_routes_in_lp'],
            color='#0f9b8e', alpha=0.75, label='MF routes in LP solution',
            bottom=0, width=0.4)
    ax2.axvline(opt_size, color='#f5a623', linewidth=2, linestyle='--')

    ax2.set_xlabel('Fleet Size (number of WW trucks)', color='white')
    ax2.set_ylabel('Mainfreight Usage', color='white')
    ax2.set_title('Mainfreight Usage vs Fleet Size', fontsize=14, pad=12)
    ax2.legend(facecolor='#16213e', edgecolor='#444466', labelcolor='white',
               fontsize=9, loc='upper right')
    ax2.grid(axis='y', color='#444466', linestyle=':', alpha=0.6)

    plt.xticks(x, [str(v) for v in x], color='white')
    fig.suptitle('Woolworths NZ — Fleet Optimisation Analysis',
                 color='white', fontsize=16, fontweight='bold', y=1.01)
    plt.tight_layout()

    output_path = f'Fixed Routes - Final/fleet_size_analysis_{day_label}.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    plt.close()
    print(f"  Plot saved to: {output_path}")
    return output_path


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Woolworths Fleet Size Analysis')
    parser.add_argument('--min_fleet', type=int, default=10)
    parser.add_argument('--max_fleet', type=int, default=24)
    parser.add_argument('--weekend',   action='store_true')
    args = parser.parse_args()

    weekday = not args.weekend
    day_label = 'saturday' if not weekday else 'weekday'

    results_df, opt_size = analyse_fleet_sizes(
        min_fleet=args.min_fleet,
        max_fleet=args.max_fleet,
        weekday=weekday,
    )

    csv_path = f'Fixed Routes - Final/fleet_size_results_{day_label}.csv'
    results_df.to_csv(csv_path, index=False)
    print(f"  Results saved to: {csv_path}")

    plot_results(results_df, opt_size, weekday=weekday)
