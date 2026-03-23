import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import ConvexHull
from sklearn.cluster import KMeans

# Load the demand data
demand_file_path = '../0_Fixed Data - Initial Setup data/storemean.csv'
demand_data = pd.read_csv(demand_file_path)

# Load the other data
other_data_file_path = 'Store_Regions_Demand_Stats.csv'
other_data = pd.read_csv(other_data_file_path)

# Rename the 'Weekday Mean' column to 'mean' for consistency
demand_data = demand_data.rename(columns={'Weekday Mean': 'mean'})

# Merge the demand data with the other data
merged_data = pd.merge(demand_data, other_data, on='Store')

# Calculate the median and standard deviation for each store
demand_stats = merged_data.groupby('Store')['mean'].agg(['median', 'std']).reset_index()

# Merge the demand statistics with the other data
merged_data_median = pd.merge(demand_stats, other_data, on='Store')

# Calculate the mean demand
demand_variability = merged_data.groupby('Store')['mean'].agg(['mean', 'std'])
merged_data_median = pd.merge(
    merged_data_median, demand_variability['mean'].reset_index(), on='Store'
)

# Identify stores that had mean above 10 at any time in the past
high_demand_stores = merged_data[merged_data['mean'] > 10]['Store'].unique()
merged_data_median['High Demand'] = merged_data_median['Store'].apply(lambda x: x in high_demand_stores)

# Extract coordinates for plotting
coordinates = merged_data_median[['Long', 'Lat']].values

# Perform KMeans clustering to identify clusters of stores
kmeans = KMeans(n_clusters=7, random_state=0).fit(coordinates)
merged_data_median['Cluster'] = kmeans.labels_

# Calculate the total mean demand sum and the standard deviation for each region (cluster)
region_stats = merged_data_median.groupby('Cluster').agg(
    total_mean_demand_sum=('mean', 'sum'),
    region_std=('std', 'mean')
).reset_index()

# Plot the mean and standard deviation on a map with latitudes and longitudes
plt.figure(figsize=(16, 20))  # Adjust size for wider and taller aspect ratio

# Plot each store as a dot
sc = plt.scatter(
    merged_data_median['Long'],
    merged_data_median['Lat'],
    c=merged_data_median['std'],  # Color by standard deviation
    cmap='viridis',
    alpha=0.6,
    s=50,
    marker='o',
)  # Use dots for markers

# Add text for the mean demand next to each point
for _, row in merged_data_median.iterrows():
    plt.text(
        row['Long'], row['Lat'], f"{row['mean']:.2f}", fontsize=8, ha='right', va='bottom'
    )

# Highlight stores that had high demand at any time by drawing a black ring around the dot
plt.scatter(
    merged_data_median.loc[merged_data_median['High Demand'], 'Long'],
    merged_data_median.loc[merged_data_median['High Demand'], 'Lat'],
    edgecolor='black',
    facecolor='none',
    s=100,
    marker='o',
    linewidth=1.5,
    label='Mean > 10 at any time',
)

# Helper function to draw a convex hull (rough circle) around clusters of stores
def draw_convex_hull(points, ax, color='blue'):
    if len(points) > 2:  # Need at least 3 points to create a convex hull
        hull = ConvexHull(points)
        hull_points = points[hull.vertices]
        plt.fill(hull_points[:, 0], hull_points[:, 1], color=color, alpha=0.2)

# Draw convex hulls around each cluster and add region stats text
unique_clusters = merged_data_median['Cluster'].unique()
for cluster_id in unique_clusters:
    cluster_points = coordinates[merged_data_median['Cluster'] == cluster_id]
    draw_convex_hull(cluster_points, plt.gca(), color='blue')

    # Get centroid of the cluster for text placement
    cluster_center = cluster_points.mean(axis=0)
    cluster_stats = region_stats[region_stats['Cluster'] == cluster_id]
    text = f"Total Mean Demand: {cluster_stats['total_mean_demand_sum'].values[0]:.2f}\nStd: {cluster_stats['region_std'].values[0]:.2f}"
    plt.text(cluster_center[0], cluster_center[1], text, fontsize=10, ha='center', va='center',
             bbox=dict(facecolor='white', alpha=0.6))

# Add colorbar for standard deviation
plt.colorbar(sc, label='Standard Deviation of Mean')
plt.title('Store Mean Characteristics by Location (Mean) with Region Stats')
plt.xlabel('Longitude')
plt.ylabel('Latitude')

# Adjust the ticks for finer increments
plt.xticks(
    ticks=np.arange(merged_data_median['Long'].min(), merged_data_median['Long'].max(), 0.05)
)
plt.yticks(
    ticks=np.arange(merged_data_median['Lat'].min(), merged_data_median['Lat'].max(), 0.05)
)

plt.grid(True)
plt.show()