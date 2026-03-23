import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# Step 1: Load the data
file_path = 'simulated_sales.csv'  # Replace with the actual file path
simulated_df = pd.read_csv(file_path)

# Step 2: Create histograms for each store group and day type
store_groups = simulated_df['Store Group'].unique()
day_types = simulated_df['Day Type'].unique()

for store in store_groups:
    plt.figure(figsize=(12, 6))
    
    for day in day_types:
        subset = simulated_df[(simulated_df['Store Group'] == store) & (simulated_df['Day Type'] == day)]
        
        sns.histplot(subset['Simulated Sales'], kde=True, bins=20, label=day, alpha=0.6)
    
    plt.title(f'Simulated Sales Histogram for {store}')
    plt.xlabel('Simulated Sales')
    plt.ylabel('Frequency')
    plt.legend(title='Day Type')
    plt.grid(True)
    plt.show()
