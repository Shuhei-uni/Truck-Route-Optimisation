import pandas as pd

# Load the CSV file
file_path = '../0_Fixed Data - Initial Setup data/storemean.csv'
data = pd.read_csv(file_path)

# Round the specified columns to integers
columns_to_round = ['Weekday Mean', 'Saturday Mean']
data[columns_to_round] = data[columns_to_round].round(0).astype(int)

# Create a 'Day' column to represent day numbers (assuming sequential days from 1 to 100)
data['Day'] = data.groupby('Store').cumcount() + 1

# Pivot the data to have stores as rows and days as columns for weekday and Saturday demands
weekday_pivot = data.pivot(index='Store', columns='Day', values='Weekday Mean')
saturday_pivot = data.pivot(index='Store', columns='Day', values='Saturday Mean')

# Save the pivoted DataFrames to new CSV files
weekday_output_file_path = '../0_Fixed Data - Initial Setup data/weekday_mean_demand.csv'
saturday_output_file_path = '../0_Fixed Data - Initial Setup data/saturday_mean_demand.csv'

weekday_pivot.to_csv(weekday_output_file_path)
saturday_pivot.to_csv(saturday_output_file_path)

weekday_output_file_path, saturday_output_file_path