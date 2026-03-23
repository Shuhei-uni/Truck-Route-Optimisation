#The purpose of this file is to remove demand values that are less than 0. It will then set them to 0.
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load the data from the CSV file (Assume it's named 'demand_data.csv')
data = pd.read_csv('./0_Non-FixedData-SimulationData/simulated_store_demand.csv')

# Define a function to replace negative values with 0
def replace_negative_values(demand):
    return max(demand, 0)

# Apply the function to both 'Weekday Simulated Demand' and 'Saturday Simulated Demand' columns
data['Weekday Simulated Demand'] = data['Weekday Simulated Demand'].apply(replace_negative_values)
data['Saturday Simulated Demand'] = data['Saturday Simulated Demand'].apply(replace_negative_values)

# Save the modified data back to a CSV file (optional)
data.to_csv('simulated_store_demand_2.csv', index=False)

# Display the modified DataFrame
print(data)

print(data['Saturday Simulated Demand'].min())