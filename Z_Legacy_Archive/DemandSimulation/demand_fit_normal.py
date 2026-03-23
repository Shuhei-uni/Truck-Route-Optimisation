import pandas as pd
import numpy as np
import scipy.stats as stats

# Step 1: Load the data
file_path = 'WoolworthsDemand2024.csv'  # Replace with your file path
df = pd.read_csv(file_path)

# Convert the date columns to rows
df_melted = df.melt(id_vars=["Store"], var_name="Date", value_name="Sales")
df_melted['Date'] = pd.to_datetime(df_melted['Date'], format='%d/%m/%Y')
df_melted['DayOfWeek'] = df_melted['Date'].dt.day_name()

# Separate into Saturdays and Weekdays
df_melted['DayType'] = df_melted['DayOfWeek'].apply(lambda x: 'Saturday' if x == 'Saturday' else 'Weekday')

# Define store groups
store_groups = {
    "FreshChoice": df[df['Store'].str.contains("FreshChoice")],
    "Metro": df[df['Store'].str.contains("Metro")],
    "SuperValue": df[df['Store'].str.contains("SuperValue")],
    "Woolworths": df[df['Store'].str.contains("Woolworths")]
}

# Function to fit a Log-Normal distribution and generate simulated values
def simulate_sales(data, num_simulations=100):
    # Filter out non-positive values
    data = data[data > 0]
    
    if len(data) > 0:
        shape, loc, scale = stats.lognorm.fit(data, floc=0)
        simulated_values = stats.lognorm.rvs(shape, loc=loc, scale=scale, size=num_simulations)
    else:
        simulated_values = np.zeros(num_simulations)  # Handle the case where no data remains
    
    return simulated_values

# Step 2: Simulate demand for each store group for weekdays and Saturdays
simulated_data = []

for group_name, group_df in store_groups.items():
    group_data = df_melted[df_melted['Store'].isin(group_df['Store'])]
    
    # Weekdays simulation
    weekdays_data = group_data[group_data['DayType'] == 'Weekday']['Sales']
    simulated_weekdays = simulate_sales(weekdays_data)
    
    # Saturdays simulation
    saturdays_data = group_data[group_data['DayType'] == 'Saturday']['Sales']
    simulated_saturdays = simulate_sales(saturdays_data)
    
    # Store the results
    simulated_data.append({
        'Store Group': group_name,
        'Day Type': 'Weekday',
        'Simulated Sales': simulated_weekdays
    })
    
    simulated_data.append({
        'Store Group': group_name,
        'Day Type': 'Saturday',
        'Simulated Sales': simulated_saturdays
    })

# Step 3: Convert to DataFrame and save as CSV
simulated_df = pd.DataFrame(simulated_data)

# Expand the 'Simulated Sales' into separate rows
simulated_df = simulated_df.explode('Simulated Sales').reset_index(drop=True)

# Save to CSV
simulated_df.to_csv('simulated_sales.csv', index=False)

print("Simulated data saved to 'simulated_sales.csv'")
