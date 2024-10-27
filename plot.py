import csv
import matplotlib.pyplot as plt
import os
import glob

def ms_to_hours(ms):
    return ms / (1000 * 60 * 60)

def process_files(base_filename):
    file_pattern = f"{base_filename}_*.csv"
    times, pressures, temperatures = [], [], []
    file_size = 0
    cumulative_time = 0

    for filename in sorted(glob.glob(file_pattern)):
        file_size += os.path.getsize(filename) / 1024

        with open(filename, 'r') as file:
            csv_reader = csv.reader(file)
            next(csv_reader)  # Skip header
            for row in csv_reader:
                time, pressure, temp = map(float, row)
                time = time / 100  # Convert to correct milliseconds
                cumulative_time += time
                times.append(ms_to_hours(cumulative_time))
                pressures.append(pressure / 100)
                temperatures.append(temp / 100)

    return times, pressures, temperatures, file_size

base_filenames = input("Enter base filenames separated by spaces (e.g., 'test1 test2 test3'): ").split()

all_times, all_pressures, all_temperatures = [], [], []
total_file_size = 0
separators = []

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(20, 12))

time_offset = 0
for i, base_filename in enumerate(base_filenames):
    times, pressures, temperatures, file_size = process_files(base_filename)
    total_file_size += file_size

    if times:
        times = [t + time_offset for t in times]
        all_times.extend(times)
        all_pressures.extend(pressures)
        all_temperatures.extend(temperatures)

        label = f"{base_filename}"
        ax1.plot(times, pressures, label=label)
        ax2.plot(times, temperatures, label=label)

        if i < len(base_filenames) - 1:
            separators.append(times[-1])
            time_offset = times[-1]

for sep in separators:
    ax1.axvline(x=sep, color='r', linestyle='--', alpha=0.2)
    ax2.axvline(x=sep, color='r', linestyle='--', alpha=0.2)

ax1.set_ylabel('Pressure (mbar)')
ax1.set_title('Pressure over Time')
ax1.legend ()

ax2.set_ylabel('Temperature (°C)')
ax2.set_title('Temperature over Time')
ax2.set_xlabel('Time (hours)')
ax2.legend()

plt.tight_layout()
output_filename = f"combined_plot_{'_'.join(base_filenames)}.png"
plt.savefig(output_filename, dpi=300, bbox_inches='tight')
print(f"Plot saved as '{output_filename}'")
print(f"Total file size processed: {total_file_size:.2f} KB")