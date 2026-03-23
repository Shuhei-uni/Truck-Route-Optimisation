import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import scipy.stats as stats
from traffic_routes_module import *
import ast

weekday_simulation = pd.read_csv('./~~~FINAL DATA STORED WITHIN/weekday_simulation_data.csv')
saturday_simulation = pd.read_csv('./~~~FINAL DATA STORED WITHIN/saturday_simulation_data.csv')

weekday_pivot = weekday_simulation.pivot(index='day', columns='region', values='total_cost')
saturday_pivot = saturday_simulation.pivot(index='day', columns='region', values='total_cost')
plt.figure(figsize=(12, 6))
weekday_pivot.plot(kind='area', stacked=True, alpha=0.7)
plt.title('Weekday Total cost over simulation days')
plt.xlabel('Simulation Day')
plt.ylabel('Total Cost')
plt.legend(title='Region')
plt.tight_layout()
#plt.show()
plt.savefig('weekday_simulation_visualization_new.png')
plt.close()
plt.figure(figsize=(12, 6))
saturday_pivot.plot(kind='area', stacked=True, alpha=0.7)
plt.title('Saturday Total cost over simulation days')
plt.xlabel('Simulation Day')
plt.ylabel('Total Cost')
plt.legend(title='Region')
plt.tight_layout()
#plt.show()
plt.savefig('saturday_simulation_visualization_new.png')
plt.close()
weekday_total_cost_per_day = weekday_simulation.groupby('day')['total_cost'].sum().to_numpy()
saturday_total_cost_per_day = saturday_simulation.groupby('day')['total_cost'].sum().to_numpy()
print(len(weekday_total_cost_per_day))
print(len(saturday_total_cost_per_day))
boxplot_data = pd.DataFrame({
    'weekday costs': weekday_total_cost_per_day,
    'Saturday costs': saturday_total_cost_per_day
})
print(boxplot_data)
df_melted = pd.melt(boxplot_data, value_vars=['weekday costs', 'Saturday costs'], var_name='simulation', value_name='Cost')
plt.figure(figsize=(8, 8))
sns.boxplot(x='simulation', y='Cost', data=df_melted)
plt.title('Simulation cost result')
plt.savefig('simulation_boxplot_new.png')

mean = np.mean(weekday_total_cost_per_day)
std_dev = np.std(weekday_total_cost_per_day, ddof=1)
confidence_level = 0.95
degrees_freedom = len(weekday_total_cost_per_day) - 1
confidence_interval = stats.t.interval(confidence_level, degrees_freedom, mean, std_dev / np.sqrt(len(weekday_total_cost_per_day)))

mean2 = np.mean(saturday_total_cost_per_day)
std_dev2 = np.std(saturday_total_cost_per_day, ddof=1)
confidence_level2 = 0.95
degrees_freedom2 = len(saturday_total_cost_per_day) - 1
confidence_interval2 = stats.t.interval(confidence_level, degrees_freedom, mean2, std_dev2 / np.sqrt(len(saturday_total_cost_per_day)))
print(mean, std_dev, confidence_interval)
print(mean2, std_dev2, confidence_interval2)
plt.close()
durations = pd.read_csv('./0_Fixed Data - Initial Setup data/WoolworthsDurations.csv')
routes = pd.read_csv('./Fixed Routes - Final/weekday_mean_data.csv')
routes = routes['routes'].apply(eval)
routes2 = pd.read_csv('./Fixed Routes - Final/saturday_mean_data.csv')
routes2 = routes2['routes'].apply(eval)
data = pd.read_csv('./0_Fixed Data - Initial Setup data/WoolworthsDemand2024.csv')
name = data['Store']
names = []
for i in range(64):
    names.append(name[i])
names.append('Distribution Centre Auckland')
def duration_traffic_based(durations):
    durations_traffic = durations.copy()
    for i in range(len(durations)):
        for j in range(len(durations.columns) - 1):
            duration = durations.iloc[i, j + 1]
            if duration != 0:
                if 1200 <= duration <= 1800:
                    new_duration = random.gauss(duration, 600)
                    if new_duration <= 0:
                        new_duration += random.uniform(1000, 1200)
                    durations_traffic.iat[i, j + 1] = new_duration
                elif duration > 1800:
                    new_duration = random.gauss(duration, 720)
                    if new_duration <= 0:
                        new_duration += random.uniform(1000, 1200)
                    durations_traffic.iat[i, j + 1] = new_duration
                elif duration < 1200:
                    new_duration = random.gauss(duration, 300)
                    if new_duration <= 0:
                        new_duration += random.uniform(1000, 1200)
                    durations_traffic.iat[i, j + 1] = new_duration
    return durations_traffic


def calculate_durations(routes, all_names, durations):
    total_durations = []
    for route in routes:
        tot_dur = 0
        for j in range(len(route) - 1):
            ind1 = all_names.index(route[j])
            ind2 = all_names.index(route[j + 1])
            duration = durations.iloc[ind1, ind2 + 1]
            tot_dur += duration
        total_durations.append(tot_dur)
    return total_durations


# num_simulations = 100
# simulation_results = np.zeros((num_simulations, durations.iloc[:, 1:].shape[0], durations.iloc[:, 1:].shape[1]))
# for sim in range(num_simulations):
#     simulation_results[sim] = duration_traffic_based(durations.iloc[:, 1:])
# mean_durations = np.mean(simulation_results, axis=0)
# std_durations = np.std(simulation_results, axis=0)
# fig, ax = plt.subplots(figsize=(14, 10))
# mean_flat = mean_durations.flatten()
# std_flat = std_durations.flatten()
# indices = np.arange(len(mean_flat))
# ax.plot(indices, mean_flat, color='blue', label='Mean Duration')
# ax.fill_between(indices, mean_flat - std_flat, mean_flat + std_flat, color='blue', alpha=0.2, label='variability')
#
# ax.set_title("Traffic Fluctuations Across 100 Simulations")
# ax.set_xlabel("65 * 65 paths")
# ax.set_ylabel("Duration in seconds")
# ax.legend()
# plt.tight_layout()
# plt.savefig('duration_fluactuations.png')
weekday_column_names = [f'Route_{i+1}' for i in range(34)]
weekday_dur_df = pd.DataFrame(np.nan, index=[], columns=weekday_column_names)
saturday_column_names = [f'Route_{i+1}' for i in range(27)]
saturday_dur_df = pd.DataFrame(np.nan, index=[], columns=saturday_column_names)
all_durations = []
for i in range(100):
    new_dur_matrix = duration_traffic_based(durations)
    total_durations = calculate_durations(routes, names, new_dur_matrix)
    saturday_durations = calculate_durations(routes2, names, new_dur_matrix)
    new_row = pd.Series(total_durations, index=weekday_dur_df.columns)
    new_row2 = pd.Series(saturday_durations, index=saturday_dur_df.columns)
    weekday_dur_df = pd.concat([weekday_dur_df, new_row.to_frame().T], ignore_index=True)
    saturday_dur_df = pd.concat([saturday_dur_df, new_row2.to_frame().T], ignore_index=True)

print(weekday_dur_df['Route_1'])
print(saturday_dur_df)
weekday_melted = weekday_dur_df.melt(var_name='routes', value_name='Time')
saturday_melted = saturday_dur_df.melt(var_name='routes', value_name='Time')
plt.figure(figsize=(12, 6))
sns.kdeplot(data=weekday_melted, x='Time', hue='routes', common_norm=False, legend=True)
plt.title("Weekday Distribution of time spend on traffic per route(exclude unloading time", fontsize=10)
plt.xlabel('Time spent on traffic(seconds)', fontsize=10)
plt.ylabel('Frequency', fontsize=10)
for route in weekday_melted['routes'].unique():
    sns.kdeplot(data=weekday_melted[weekday_melted['routes'] == route], x='Time', label=route)
plt.legend(title='Routes', fontsize=7, ncol=1, bbox_to_anchor=(1, 1.15), loc='upper left')
#plt.savefig('weekday_time_distribution.png')
plt.close()

plt.figure(figsize=(12, 6))
sns.kdeplot(data=saturday_melted, x='Time', hue='routes', common_norm=False, legend=True)
plt.title("Saturday Distribution of time spend on traffic per route(exclude unloading time", fontsize=10)
plt.xlabel('Time spent on traffic(seconds)', fontsize=10)
plt.ylabel('Frequency', fontsize=10)
for route in saturday_melted['routes'].unique():
    sns.kdeplot(data=saturday_melted[saturday_melted['routes'] == route], x='Time', label=route)
plt.legend(title='Routes', fontsize=7, ncol=1, bbox_to_anchor=(1, 1.15), loc='upper left')
#plt.savefig('saturday_time_distribution.png')
plt.close()


