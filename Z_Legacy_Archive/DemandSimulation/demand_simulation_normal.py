import numpy as np
import pandas as pd
file_path = 'C:/Users/jacks/Downloads/Auckland/2024 s2/263 - ops/MeanAndStandardDeviations.csv'

def simulate_demands(df, n_simulations):
    """
    Simulates demands for weekdays and Saturdays based on the means and standard deviations in the DataFrame.

    Parameters:
        df (pandas.DataFrame): The DataFrame containing store names, means, and standard deviations.
        n_simulations (int): The number of simulations to generate per store.

    Returns:
        pandas.DataFrame: A DataFrame containing the simulated demands.
    """
    # Create empty lists to store the results
    store_names = []
    weekday_simulations = []
    saturday_simulations = []

    # Loop through each row in the DataFrame to generate simulated demands
    for index, row in df.iterrows():
        store = row['Store']
        weekday_mean = row['Weekday Mean']
        weekday_sd = row['Weekday SD']
        saturday_mean = row['Saturday Mean']
        saturday_sd = row['Saturday SD']
        
        # Bug 5 fix: Normal distribution can produce negative values. Clip to 0 and round to whole pallets.
        weekday_demand = np.maximum(0, np.round(np.random.normal(weekday_mean, weekday_sd, n_simulations))).astype(int)
        saturday_demand = np.maximum(0, np.round(np.random.normal(saturday_mean, saturday_sd, n_simulations))).astype(int)
        
        # Append the results to the lists
        store_names.extend([store] * n_simulations)
        weekday_simulations.extend(weekday_demand)
        saturday_simulations.extend(saturday_demand)

    # Create a new DataFrame with the simulated data
    simulated_df = pd.DataFrame({
        'Store': store_names,
        'Weekday Simulated Demand': weekday_simulations,
        'Saturday Simulated Demand': saturday_simulations
    })

    return simulated_df

# Read the CSV file into a DataFrame
#df = pd.read_csv('store_demand.csv')
df = pd.read_csv(file_path)

# Set the number of simulations
n_simulations = 100

# Call the function to generate simulated demands
simulated_df = simulate_demands(df, n_simulations)

# Display the new DataFrame
print(simulated_df)

# Optionally, save the simulated data to a new CSV file
simulated_df.to_csv('C:/Users/jacks/Downloads/Auckland/2024 s2/263 - ops/simulated_store_demand.csv', index=False)
