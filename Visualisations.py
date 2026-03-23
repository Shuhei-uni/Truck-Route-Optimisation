"""
Visualisations.py
=================
Generates 4 publication-quality plots for the Woolworths routing project:

  1. master_schedule_plot.png  — Route-store assignment heatmap (WW vs Mainfreight)
  2. store_demand_plot.png     — Per-store mean demand with SimCI bands and distribution
  3. fleet_size_plot.png       — Total annual cost curve with cost breakdown
  4. shift_schedule_plot.png   — Gantt chart of truck shift assignments

Usage:
    python Visualisations.py
    python Visualisations.py --out "Fixed Routes - Final"  # custom output folder

Pre-requisites (run in order first):
    python Global_LP.py
    python Fleet_Size_Analysis.py
    python Shift_Scheduler.py
"""

import ast
import argparse
import textwrap
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
from matplotlib.patches import FancyArrowPatch
import warnings
warnings.filterwarnings('ignore')

# ---------------------------------------------------------------------------
# Shared style constants
# ---------------------------------------------------------------------------
BG_DARK   = '#0d1117'
BG_PANEL  = '#161b22'
BG_PANEL2 = '#1c2128'
COL_GRID  = '#30363d'
COL_TEXT  = '#e6edf3'
COL_MUT   = '#8b949e'
COL_WW    = '#2ea043'      # green  — Woolworths
COL_MF    = '#e94560'      # red    — Mainfreight
COL_TOTAL = '#f0c040'      # yellow — total cost line
COL_MAINT = '#388bfd'      # blue   — maintenance
COL_ROUTE = '#bc8cff'      # purple — routing cost
COL_CI    = '#ffffff'

FONT_TITLE  = dict(color=COL_TEXT,  fontsize=14, fontweight='bold', pad=14)
FONT_LABEL  = dict(color=COL_MUT,   fontsize=10)
FONT_TICK   = dict(colors=COL_MUT,  labelsize=8)

def _style_ax(ax):
    ax.set_facecolor(BG_PANEL)
    ax.tick_params(**FONT_TICK)
    ax.xaxis.label.set_color(COL_MUT)
    ax.yaxis.label.set_color(COL_MUT)
    for spine in ax.spines.values():
        spine.set_edgecolor(COL_GRID)
    ax.grid(color=COL_GRID, linestyle=':', alpha=0.6)

def _fig(w, h):
    fig = plt.figure(figsize=(w, h), facecolor=BG_DARK)
    return fig


# ===========================================================================
# Plot 1 — Master Schedule: route × store assignment heatmap
# ===========================================================================
def plot_master_schedule(master_csv='Fixed Routes - Final/master_schedule.csv',
                         outdir='Fixed Routes - Final'):
    df = pd.read_csv(master_csv)
    df['route_list'] = df['route'].apply(ast.literal_eval)

    DEPOT = 'Distribution Centre Auckland'
    all_stores = sorted(set(
        s for rl in df['route_list'] for s in rl if s != DEPOT
    ))

    # Short store labels
    def shorten(name):
        name = name.replace('Distribution Centre Auckland', 'DEPOT')
        name = name.replace('Woolworths ', 'WW ')
        name = name.replace('FreshChoice ', 'FC ')
        name = name.replace('SuperValue ', 'SV ')
        name = name.replace('Metro ', 'M ')
        return name

    short_stores = [shorten(s) for s in all_stores]

    # Build matrix: rows = stores, cols = routes
    n_routes = len(df)
    matrix = np.zeros((len(all_stores), n_routes), dtype=float)
    route_labels = []
    colors_route = []

    for j, (_, row) in enumerate(df.iterrows()):
        is_ww = row['assigned_to'] == 'WW'
        colors_route.append(COL_WW if is_ww else COL_MF)
        visit_stores = [s for s in row['route_list'] if s != DEPOT]
        region = int(row['region'])
        label = f"R{region}-{'W' if is_ww else 'M'}{j+1:02d}"
        route_labels.append(label)
        for s in visit_stores:
            if s in all_stores:
                idx = all_stores.index(s)
                matrix[idx, j] = 1.0 if is_ww else 0.5

    fig = _fig(max(16, n_routes * 0.45 + 3), max(12, len(all_stores) * 0.28 + 2))
    ax = fig.add_subplot(111)
    ax.set_facecolor(BG_PANEL)

    # Heatmap — WW=green, MF=red, empty=dark
    cmap = matplotlib.colors.ListedColormap([BG_PANEL2, COL_MF, COL_WW])
    bounds = [-0.1, 0.25, 0.75, 1.05]
    norm   = matplotlib.colors.BoundaryNorm(bounds, cmap.N)
    ax.imshow(matrix, aspect='auto', cmap=cmap, norm=norm,
              interpolation='none', origin='upper')

    # Column headers (route labels), coloured by type
    ax.set_xticks(range(n_routes))
    ax.set_xticklabels(route_labels, rotation=75, ha='right',
                       fontsize=7.5, color=COL_MUT)
    for tick, col in zip(ax.get_xticklabels(), colors_route):
        tick.set_color(col)

    # Row labels (store names)
    ax.set_yticks(range(len(all_stores)))
    ax.set_yticklabels(short_stores, fontsize=8, color=COL_TEXT)

    # Colour column headers by region
    region_colors = [
        '#388bfd','#2ea043','#e94560','#f0c040',
        '#bc8cff','#ff7b72','#79c0ff','#56d364'
    ]
    for j, (_, row) in enumerate(df.iterrows()):
        region = int(row['region'])
        ax.get_xticklabels()[j].set_color(region_colors[region % 8])

    # Thin grid lines between cells
    for x in np.arange(-0.5, n_routes, 1):
        ax.axvline(x, color=BG_DARK, lw=0.5)
    for y in np.arange(-0.5, len(all_stores), 1):
        ax.axhline(y, color=BG_DARK, lw=0.5)

    # Legend
    patches = [
        mpatches.Patch(color=COL_WW, label='WW route visits store'),
        mpatches.Patch(color=COL_MF, label='Mainfreight route visits store'),
        mpatches.Patch(color=BG_PANEL2, label='Store not on this route'),
    ]
    ax.legend(handles=patches, loc='upper right',
              facecolor=BG_PANEL, edgecolor=COL_GRID,
              labelcolor=COL_TEXT, fontsize=8)

    ww_n = (df['assigned_to'] == 'WW').sum()
    mf_n = (df['assigned_to'] == 'Mainfreight').sum()
    ax.set_title(
        f'Master Schedule — Route × Store Assignment  '
        f'({ww_n} WW routes  |  {mf_n} Mainfreight routes  |  {len(all_stores)} stores)',
        **FONT_TITLE
    )
    ax.set_xlabel('Routes  (coloured by region)', **FONT_LABEL)
    ax.set_ylabel('Stores', **FONT_LABEL)
    fig.patch.set_facecolor(BG_DARK)

    plt.tight_layout()
    out = f'{outdir}/master_schedule_plot.png'
    fig.savefig(out, dpi=150, bbox_inches='tight', facecolor=BG_DARK)
    plt.close(fig)
    print(f'  [1/4] Saved: {out}')
    return out


# ===========================================================================
# Plot 2 — Store Demand: mean + std distribution across 100 simulated days
# ===========================================================================
def plot_store_demand(demand_csv='0_Non-FixedData-SimulationData/weekday_simulation_demand.csv',
                      outdir='Fixed Routes - Final'):
    df = pd.read_csv(demand_csv, index_col='Store')

    means = df.mean(axis=1).sort_values(ascending=False)
    stds  = df.std(axis=1).loc[means.index]
    p25   = df.quantile(0.25, axis=1).loc[means.index]
    p75   = df.quantile(0.75, axis=1).loc[means.index]
    p95   = df.quantile(0.95, axis=1).loc[means.index]

    n = len(means)
    xs = np.arange(n)

    fig = _fig(18, 7)
    ax  = fig.add_subplot(111)
    _style_ax(ax)

    # 95th percentile band
    ax.fill_between(xs, p25.values, p95.values,
                    alpha=0.18, color=COL_WW, label='IQR + 95th pct band')
    ax.fill_between(xs, p25.values, p75.values,
                    alpha=0.35, color=COL_WW)

    # Mean bars
    bars = ax.bar(xs, means.values, color=COL_WW, alpha=0.85, width=0.6,
                  label='Mean daily demand (pallets)', zorder=3)

    # Std error caps
    ax.errorbar(xs, means.values, yerr=stds.values,
                fmt='none', color=COL_TEXT, alpha=0.5,
                capsize=3, elinewidth=1)

    # Capacity line
    ax.axhline(20, color=COL_MF, linewidth=1.8, linestyle='--',
               label='Truck capacity (20 pallets)', zorder=4)

    # Annotations at top
    ax.set_xticks(xs)
    labels = [
        s.replace('Woolworths ', 'WW ')
         .replace('FreshChoice ', 'FC ')
         .replace('SuperValue ', 'SV ')
         .replace('Metro ', 'M ')
        for s in means.index
    ]
    ax.set_xticklabels(labels, rotation=55, ha='right', fontsize=7.5, color=COL_TEXT)

    ax.yaxis.set_major_locator(mticker.MultipleLocator(2))
    ax.set_ylabel('Pallets / day', **FONT_LABEL)
    ax.set_title('Simulated Store Demand  (100 weekdays)  —  mean ± std, IQR, 95th pct', **FONT_TITLE)
    ax.legend(facecolor=BG_PANEL, edgecolor=COL_GRID, labelcolor=COL_TEXT, fontsize=9)
    ax.set_xlim(-0.7, n - 0.3)

    fig.patch.set_facecolor(BG_DARK)
    plt.tight_layout()
    out = f'{outdir}/store_demand_plot.png'
    fig.savefig(out, dpi=150, bbox_inches='tight', facecolor=BG_DARK)
    plt.close(fig)
    print(f'  [2/4] Saved: {out}')
    return out


# ===========================================================================
# Plot 3 — Optimal Fleet Size: cost curve with breakdown
# ===========================================================================
def plot_fleet_size(results_csv='Fixed Routes - Final/fleet_size_results_weekday.csv',
                    outdir='Fixed Routes - Final'):
    df = pd.read_csv(results_csv)

    x         = df['fleet_size']
    total     = df['total_annual_cost ($)'] / 1e6
    maint     = df['annual_maintenance ($)'] / 1e6
    routing   = df['annual_routing_cost ($)'] / 1e6
    ci        = df['ci_95_annual ($)'] / 1e6
    mf_pct    = df['mf_days_pct (%)']
    mf_lp     = df['mf_routes_in_lp']

    opt_idx   = df['total_annual_cost ($)'].idxmin()
    opt_size  = int(df.loc[opt_idx, 'fleet_size'])
    opt_cost  = total.iloc[opt_idx]

    fig = _fig(13, 10)
    gs  = fig.add_gridspec(3, 1, hspace=0.08,
                           height_ratios=[2.5, 1, 1])
    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1], sharex=ax1)
    ax3 = fig.add_subplot(gs[2], sharex=ax1)

    for ax in (ax1, ax2, ax3):
        _style_ax(ax)

    # --- top: total cost breakdown ---
    ax1.stackplot(x, maint, routing, labels=['Fleet maintenance', 'Routing cost'],
                  colors=[COL_MAINT, COL_ROUTE], alpha=0.4)
    ax1.plot(x, total, color=COL_TOTAL, lw=2.5, marker='o', ms=6,
             label='Total annual cost', zorder=5)
    ax1.fill_between(x, total - ci, total + ci,
                     color=COL_CI, alpha=0.1, label='95% CI')

    ax1.axvline(opt_size, color=COL_TOTAL, lw=1.8, ls='--', alpha=0.8)
    ax1.annotate(
        f'  Optimal\n  {opt_size} trucks\n  ${opt_cost:.2f}M',
        xy=(opt_size, opt_cost),
        xytext=(opt_size + 0.5, opt_cost + 0.3),
        color=COL_TOTAL, fontsize=9, fontweight='bold',
        arrowprops=dict(arrowstyle='->', color=COL_TOTAL, lw=1.2)
    )
    ax1.yaxis.set_major_formatter(mticker.FormatStrFormatter('$%.1fM'))
    ax1.set_ylabel('Annual Cost', **FONT_LABEL)
    ax1.set_title('Woolworths NZ — Fleet Optimisation: Total Annual Cost vs Fleet Size',
                  **FONT_TITLE)
    ax1.legend(facecolor=BG_PANEL, edgecolor=COL_GRID, labelcolor=COL_TEXT,
               fontsize=9, loc='upper left')
    plt.setp(ax1.get_xticklabels(), visible=False)

    # --- middle: MF overflow days ---
    ax2.bar(x, mf_pct, color=COL_MF, alpha=0.8, width=0.6)
    ax2.axvline(opt_size, color=COL_TOTAL, lw=1.8, ls='--', alpha=0.8)
    ax2.set_ylabel('% days MF\noverflow', **FONT_LABEL)
    ax2.yaxis.set_major_formatter(mticker.FormatStrFormatter('%.0f%%'))
    ax2.set_ylim(0, 105)
    plt.setp(ax2.get_xticklabels(), visible=False)

    # --- bottom: MF routes in LP solution ---
    ax3.bar(x, mf_lp, color=COL_MF, alpha=0.55, width=0.6)
    ax3.axvline(opt_size, color=COL_TOTAL, lw=1.8, ls='--', alpha=0.8)
    ax3.set_ylabel('MF routes\nin LP', **FONT_LABEL)
    ax3.set_xlabel('Fleet Size (WW trucks)', **FONT_LABEL)
    ax3.set_xticks(x)

    fig.patch.set_facecolor(BG_DARK)
    plt.tight_layout()
    out = f'{outdir}/fleet_size_plot.png'
    fig.savefig(out, dpi=150, bbox_inches='tight', facecolor=BG_DARK)
    plt.close(fig)
    print(f'  [3/4] Saved: {out}')
    return out


# ===========================================================================
# Plot 4 — Shift Schedule: Gantt chart
# ===========================================================================
def plot_shift_schedule(schedule_csv='Fixed Routes - Final/shift_schedule.csv',
                        outdir='Fixed Routes - Final'):
    df = pd.read_csv(schedule_csv)
    df['route_list'] = df['route'].apply(ast.literal_eval)

    DEPOT = 'Distribution Centre Auckland'

    def shorten_route(route_list):
        stops = [s for s in route_list if s != DEPOT]
        short = [
            s.replace('Woolworths ', 'WW ')
             .replace('FreshChoice ', 'FC ')
             .replace('SuperValue ', 'SV ')
             .replace('Metro ', 'M ')
            for s in stops
        ]
        return ' → '.join(short)

    trucks  = sorted(df['truck_id'].unique())
    n_trucks = len(trucks)
    truck_idx = {t: i for i, t in enumerate(trucks)}

    SHIFT_START = {1: 8 * 3600, 2: 14 * 3600}   # 8am, 2pm in seconds from midnight
    SHIFT_DUR   = 14400                            # 4-hour nominal shift

    # Region colour palette
    region_colors = [
        '#388bfd','#2ea043','#e94560','#f0c040',
        '#bc8cff','#ff7b72','#79c0ff','#56d364'
    ]

    fig = _fig(16, max(6, n_trucks * 0.9 + 2))
    ax  = fig.add_subplot(111)
    _style_ax(ax)
    ax.set_xlim(7 * 3600, 22 * 3600)   # 7am to 10pm

    for _, row in df.iterrows():
        truck_i = truck_idx[row['truck_id']]
        shift   = int(row['shift'])
        start   = SHIFT_START[shift]
        dur     = row['duration_sec']
        region  = int(row['region'])
        ot_sec  = row['overtime_sec']
        col     = region_colors[region % 8]

        # Normal part
        normal_dur = min(dur, SHIFT_DUR)
        ax.barh(truck_i, normal_dur, left=start, height=0.55,
                color=col, alpha=0.85, linewidth=0.5, edgecolor=BG_DARK)

        # Overtime part
        if ot_sec > 0:
            ot_start = start + SHIFT_DUR
            ax.barh(truck_i, ot_sec, left=ot_start, height=0.55,
                    color=COL_MF, alpha=0.75, linewidth=0.5, edgecolor=BG_DARK,
                    hatch='///')

        # Label inside bar
        label = shorten_route(row['route_list'])
        label_wrapped = textwrap.shorten(label, width=35, placeholder='…')
        bar_center = start + dur / 2
        ax.text(bar_center, truck_i, label_wrapped,
                ha='center', va='center', fontsize=5.5,
                color='white', fontweight='bold', clip_on=True)

    # Shift boundary lines
    for shift, t in SHIFT_START.items():
        ax.axvline(t, color=COL_GRID, lw=1.2, ls='--', alpha=0.7)
        ax.text(t + 150, n_trucks - 0.3,
                f'Shift {shift} start\n({8 if shift==1 else 14}:00)',
                color=COL_MUT, fontsize=7.5, va='top')
    # Shift end lines
    for shift, t in SHIFT_START.items():
        ax.axvline(t + SHIFT_DUR, color=COL_GRID, lw=0.8, ls=':', alpha=0.5)

    # Y-axis: truck labels
    ax.set_yticks(range(n_trucks))
    ax.set_yticklabels([f'Truck {t}' for t in trucks], fontsize=8.5, color=COL_TEXT)
    ax.set_ylim(-0.7, n_trucks - 0.3)

    # X-axis: hours
    hour_ticks = range(7 * 3600, 22 * 3600 + 1, 3600)
    ax.set_xticks(hour_ticks)
    ax.set_xticklabels([f'{h//3600}:00' for h in hour_ticks],
                       fontsize=8, color=COL_MUT)

    # Region legend patches
    region_names = [f'Region {r}' for r in range(8)]
    region_patches = [
        mpatches.Patch(color=region_colors[r], label=region_names[r], alpha=0.85)
        for r in range(8)
    ]
    ot_patch = mpatches.Patch(color=COL_MF, alpha=0.75, hatch='///', label='Overtime')
    ax.legend(handles=region_patches + [ot_patch],
              facecolor=BG_PANEL, edgecolor=COL_GRID, labelcolor=COL_TEXT,
              fontsize=8, loc='lower right', ncol=3)

    ax.set_xlabel('Time of day', **FONT_LABEL)
    ax.set_title('Daily Shift Schedule — Truck Route Assignments (Gantt)',
                 **FONT_TITLE)

    fig.patch.set_facecolor(BG_DARK)
    plt.tight_layout()
    out = f'{outdir}/shift_schedule_plot.png'
    fig.savefig(out, dpi=150, bbox_inches='tight', facecolor=BG_DARK)
    plt.close(fig)
    print(f'  [4/4] Saved: {out}')
    return out


# ===========================================================================
# Main
# ===========================================================================
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Woolworths Routing Visualisations')
    parser.add_argument('--out', type=str, default='Fixed Routes - Final')
    args = parser.parse_args()

    print(f"\n{'='*52}")
    print(f"  Generating visualisations → {args.out}/")
    print(f"{'='*52}")

    paths = []
    paths.append(plot_master_schedule(outdir=args.out))
    paths.append(plot_store_demand(outdir=args.out))
    paths.append(plot_fleet_size(outdir=args.out))
    paths.append(plot_shift_schedule(outdir=args.out))

    print(f"\n  Done. {len(paths)} plots saved:")
    for p in paths:
        print(f"    {p}")
    print(f"{'='*52}\n")
