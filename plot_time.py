import csv
import matplotlib.pyplot as plt
import os
import glob
import sys
import numpy as np

def seconds_to_ms(seconds):
    return seconds * 1000

def process_files(base_filename, start_time, end_time):
    file_pattern = f"{base_filename}_*.csv"
    times, pressures, temperatures = [], [], []
    file_size = 0
    cumulative_time = 0
    
    # Convert input time range to milliseconds
    start_time_ms = seconds_to_ms(start_time)
    end_time_ms = seconds_to_ms(end_time)

    for filename in sorted(glob.glob(file_pattern)):
        file_size += os.path.getsize(filename) / 1024

        with open(filename, 'r') as file:
            csv_reader = csv.reader(file)
            next(csv_reader)  # Skip header
            for row in csv_reader:
                time, pressure, temp = map(float, row)
                time = time / 100  # Convert to correct milliseconds
                cumulative_time += time
                
                if start_time_ms <= cumulative_time <= end_time_ms:
                    times.append(cumulative_time)  # Store time in milliseconds
                    pressures.append(pressure / 100)
                    temperatures.append(temp / 100)

    return times, pressures, temperatures, file_size

def set_custom_ticks(ax, times):
    # Create ticks every 100ms
    min_time = min(times)
    max_time = max(times)
    # Round to nearest 100ms
    tick_start = np.ceil(min_time / 100) * 100
    tick_end = np.floor(max_time / 100) * 100
    minor_ticks = np.arange(tick_start, tick_end + 100, 100)
    
    # Create labels every 500ms
    major_ticks = np.arange(tick_start, tick_end + 500, 500)
    
    # Set the ticks and labels
    ax.set_xticks(minor_ticks, minor=True)
    ax.set_xticks(major_ticks)
    
    # Only show labels for major ticks
    ax.set_xticklabels([f'{int(x)}' for x in major_ticks])
    
    # Adjust tick parameters
    ax.tick_params(axis='x', which='minor', length=4)
    ax.tick_params(axis='x', which='major', length=8)
    
    # Add grid for major ticks only
    ax.grid(True, axis='x', which='major', linestyle='--', alpha=0.5)

def plot_data(base_filename, start_time, end_time):
    times, pressures, temperatures, total_file_size = process_files(base_filename, start_time, end_time)

    if not times:
        print(f"No data points found in the specified time range for {base_filename}.")
        return

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(20, 12))

    # Plot with milliseconds on x-axis
    ax1.plot(times, pressures, label=base_filename)
    ax1.set_ylabel('Pressure (mbar)')
    ax1.set_title(f'Pressure over Time ({start_time} to {end_time} seconds)')
    ax1.legend()
    ax1.set_xlabel('Time (milliseconds)')
    
    # Set custom ticks for both plots
    set_custom_ticks(ax1, times)
    
    ax2.plot(times, temperatures, label=base_filename)
    ax2.set_ylabel('Temperature (°C)')
    ax2.set_xlabel('Time (milliseconds)')
    ax2.set_title(f'Temperature over Time ({start_time} to {end_time} seconds)')
    ax2.legend()
    
    set_custom_ticks(ax2, times)

    # Add text box with input parameters
    input_text = f"Input Parameters:\nBase Filename: {base_filename}\nStart Time: {start_time} seconds\nEnd Time: {end_time} seconds"
    plt.figtext(0.02, 0.02, input_text,
                bbox=dict(facecolor='white', edgecolor='black', alpha=0.8),
                fontsize=10, family='monospace')

    plt.tight_layout()
    # Adjust subplot spacing to make room for the text box
    plt.subplots_adjust(bottom=0.15)
    
    output_filename = f"{base_filename}_{start_time}to{end_time}seconds.png"
    plt.savefig(output_filename, dpi=300, bbox_inches='tight')
    print(f"Plot saved as '{output_filename}'")
    print(f"Total file size processed: {total_file_size:.2f} KB")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python script.py <base_filename> <start_time_seconds> <end_time_seconds>")
        sys.exit(1)

    base_filename = sys.argv[1]
    start_time = float(sys.argv[2])
    end_time = float(sys.argv[3])

    plot_data(base_filename, start_time, end_time)