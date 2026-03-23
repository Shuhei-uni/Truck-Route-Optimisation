import pandas as pd

# Load the guideline file
guideline_path = 'guideline_region_stores.txt'
sorted_stores_path = 'Reordered_Sorted_Stores_by_Region.csv'
store_mean_path = '../0_Fixed Data - Initial Setup data/storemean.csv'

# Read the guideline file
with open(guideline_path, 'r') as file:
    guideline_data = file.read()

# Parse the guideline data
cluster_map = {}
current_cluster = None

# Split the guideline data by lines
lines = guideline_data.split('\n')
for line in lines:
    line = line.strip()
    if line.startswith('Cluster'):
        # Extract cluster number
        current_cluster = int(line.split(':')[0].split(' ')[1])
    elif line:
        # Add store to the current cluster
        cluster_map[line] = current_cluster

# Load the sorted stores data
sorted_stores_df = pd.read_csv(sorted_stores_path)

# Add a new column to the DataFrame for cluster number
sorted_stores_df['Cluster'] = sorted_stores_df['Store'].map(cluster_map)

# Sort the DataFrame by the cluster number
sorted_stores_df = sorted_stores_df.sort_values(by='Cluster').reset_index(drop=True)

# Save the reordered DataFrame to a new CSV file
reordered_path = 'Reordered_Sorted_Stores_by_Region.csv'
sorted_stores_df.to_csv(reordered_path, index=False)

# Load the store mean data
store_mean_df = pd.read_csv(store_mean_path)

# Map each store to its cluster
store_mean_df['Cluster'] = store_mean_df['Store'].map(cluster_map)

# Calculate total weekday mean for each cluster
weekday_total = store_mean_df.groupby('Cluster')['Weekday Mean'].sum().rename('Weekday Mean Total')

# Calculate total Saturday mean for each cluster
saturday_total = store_mean_df.groupby('Cluster')['Saturday Mean'].sum().rename('Saturday Mean Total')

# Set the store name as the index
store_mean_df.set_index('Store', inplace=True)

# Add cluster total statistics to the DataFrame
store_mean_df['Cluster Weekday Mean Total'] = store_mean_df['Cluster'].map(weekday_total)
store_mean_df['Cluster Saturday Mean Total'] = store_mean_df['Cluster'].map(saturday_total)

# Create an array for the number of trucks per cluster

# Number of trucks per cluster -- REVERSING ORDER TO MATCH THE CLUSTER NUMBER
# [7, 6, 5, 4, 3, 2, 1, 0]
num_trucks_per_cluster = [2, 3, 4, 3, 2, 3, 2, 5]



# Sort the DataFrame by the cluster number
store_mean_df = store_mean_df.sort_values(by='Cluster')

# Add the number of trucks per cluster to the DataFrame
store_mean_df['Number of Trucks'] = store_mean_df['Cluster'].map(lambda x: num_trucks_per_cluster[x - 1])

store_mean_df.to_csv('All_info.csv', index=True)
