import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load the data from the CSV file (Assume it's named 'demand_data.csv')
data = pd.read_csv('./0_Non-FixedData-SimulationData/simulated_store_demand_2.csv')

# Assuming you need to add a 'Group' column to the DataFrame
store_groups = {
    'FreshChoice': 'FreshChoice',
    'Metro': 'Metro',
    'SuperValue': 'SuperValue',
    'Woolworths': 'Woolworths'
}
# Example: Adding a group manually based on store names
data['Group'] = data['Store'].apply(lambda x: next((group for key, group in store_groups.items() if key in x), 'Other'))

# Melt the data to make it easier to plot
melted_data = pd.melt(data, id_vars=["Store", "Group"], 
                      value_vars=["Weekday Simulated Demand", "Saturday Simulated Demand"],
                      var_name="Day", value_name="Demand")

# Create box plots to compare weekday and Saturday demand for each store group
plt.figure(figsize=(12, 8))
sns.boxplot(x="Group", y="Demand", hue="Day", data=melted_data)

# Add title and labels
plt.title('Simulated Demand by Store Group: Weekdays vs Saturdays')
plt.xlabel('Store Group')
plt.ylabel('Simulated Demand')

# Optionally, you can adjust the xticks if necessary
plt.xticks(rotation=45)

# Display the plot
plt.show()
