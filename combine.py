import pandas as pd

# Load the data
data = pd.read_csv("data8_divided.csv")

data['Time'] = data['Time'].cumsum()
data['Time'] = data['Time'].round(2)


# Save the modified data to a new CSV file
data.to_csv("data8_real_time.csv", index=False)

print("Time column converted to cumulative real time and saved to data8_real_time.csv.")
