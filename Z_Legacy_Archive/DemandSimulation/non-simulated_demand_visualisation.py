import pandas as pd
import matplotlib.pyplot as plt

# Ensure the file path is correct
file_path = 'WoolworthsDemand2024.csv'

# Read the CSV file
try:
    df = pd.read_csv(file_path)
except FileNotFoundError:
    print(f"Error: The file '{file_path}' does not exist.")
    exit()

# Extract the store type from the store name
df['StoreType'] = df['Store'].apply(lambda x: x.split()[0])

# Define unique store types
store_types = df['StoreType'].unique()

# Convert dates to numerical weekday and Saturday columns
date_columns = [col for col in df.columns[1:] if pd.to_datetime(col, errors='coerce', dayfirst=True) is not pd.NaT]
weekday_columns = [col for col in date_columns if pd.to_datetime(col, errors='coerce', dayfirst=True).weekday() < 5]
saturday_columns = [col for col in date_columns if pd.to_datetime(col, errors='coerce', dayfirst=True).weekday() == 5]

# Plot histograms for each store type
for store_type in store_types:
    store_data = df[df['StoreType'] == store_type]

    # Weekday sales
    weekday_sales = store_data[weekday_columns].values.flatten()

    # Saturday sales
    saturday_sales = store_data[saturday_columns].values.flatten()

    # Plot histograms
    plt.figure(figsize=(10, 5))

    # Weekdays
    plt.subplot(1, 2, 1)
    plt.hist(weekday_sales, bins=20, color='blue', alpha=0.7)
    plt.title(f'{store_type} - Weekdays')
    plt.xlabel('Sales')
    plt.ylabel('Frequency')

    # Saturdays
    plt.subplot(1, 2, 2)
    plt.hist(saturday_sales, bins=20, color='green', alpha=0.7)
    plt.title(f'{store_type} - Saturdays')
    plt.xlabel('Sales')
    plt.ylabel('Frequency')

    # Show the plots
    plt.tight_layout()
    plt.show()
