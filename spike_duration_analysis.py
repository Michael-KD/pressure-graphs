import csv
import matplotlib.pyplot as plt
import sys
import glob
import numpy as np
from scipy.signal import find_peaks

def process_files(base_filename):
    file_pattern = f"{base_filename}_*.csv"
    times, pressures = [], []
    cumulative_time = 0
    
    for filename in sorted(glob.glob(file_pattern)):
        with open(filename, 'r') as file:
            csv_reader = csv.reader(file)
            next(csv_reader)  # Skip header
            for row in csv_reader:
                time, pressure, _ = map(float, row)
                time = time / 100  # Convert to correct milliseconds
                cumulative_time += time
                times.append(cumulative_time)
                pressures.append(pressure / 100)

    return np.array(times), np.array(pressures)

def find_ambient_pressure(times, pressures, peak_idx):
    # Find the index 100ms before the peak
    peak_time = times[peak_idx]
    ambient_idx = np.argmin(np.abs(times - (peak_time - 100)))
    return pressures[ambient_idx]

def find_spike_durations(times, pressures):
    # Find high spikes (>1200 mbar)
    high_peaks, _ = find_peaks(pressures, height=1200, distance=1000)
    
    # Find low spikes (>840 mbar but <1200 mbar)
    low_peaks, _ = find_peaks(pressures, height=840, distance=1000)
    low_peaks = [peak for peak in low_peaks if pressures[peak] < 1200]
    
    spike_data = []
    
    # First process high peaks
    for peak_idx in high_peaks:
        peak_time = times[peak_idx]
        peak_pressure = pressures[peak_idx]
        ambient_pressure = find_ambient_pressure(times, pressures, peak_idx)
        
        # Look forward from peak to find where pressure returns to ambient
        for j in range(peak_idx, len(pressures)):
            if pressures[j] <= ambient_pressure:
                crossing_time = times[j]
                duration = crossing_time - peak_time
                spike_data.append({
                    'peak_idx': peak_idx,
                    'peak_time': peak_time,
                    'peak_pressure': peak_pressure,
                    'crossing_time': crossing_time,
                    'duration': duration,
                    'type': 'high',
                    'ambient_pressure': ambient_pressure
                })
                break
    
    # Then process low peaks
    for peak_idx in low_peaks:
        peak_time = times[peak_idx]
        peak_pressure = pressures[peak_idx]
        ambient_pressure = find_ambient_pressure(times, pressures, peak_idx)
        
        # Look forward from peak to find where pressure returns to ambient
        for j in range(peak_idx, len(pressures)):
            if pressures[j] <= ambient_pressure:
                crossing_time = times[j]
                duration = crossing_time - peak_time
                spike_data.append({
                    'peak_idx': peak_idx,
                    'peak_time': peak_time,
                    'peak_pressure': peak_pressure,
                    'crossing_time': crossing_time,
                    'duration': duration,
                    'type': 'low',
                    'ambient_pressure': ambient_pressure
                })
                break
    
    return spike_data

def plot_spikes(times, pressures, spike_data, base_filename):
    fig, axes = plt.subplots(2, 2, figsize=(20, 16))
    axes = axes.flatten()
    
    # Sort spikes so high pressure spikes are 1 and 3, low pressure are 2 and 4
    high_spikes = [s for s in spike_data if s['type'] == 'high']
    low_spikes = [s for s in spike_data if s['type'] == 'low']
    
    # Interleave high and low spikes
    sorted_spikes = []
    for i in range(max(len(high_spikes), len(low_spikes))):
        if i < len(high_spikes):
            sorted_spikes.append(high_spikes[i])
        if i < len(low_spikes):
            sorted_spikes.append(low_spikes[i])
    
    for i, spike in enumerate(sorted_spikes):
        # Calculate window around spike
        window_size = 400 if spike['type'] == 'low' else 600
        window_start = max(0, spike['peak_time'] - window_size)
        window_end = min(max(times), spike['crossing_time'] + window_size)
        
        # Get data within window
        window_mask = (np.array(times) >= window_start) & (np.array(times) <= window_end)
        window_times = np.array(times)[window_mask]
        window_pressures = np.array(pressures)[window_mask]
        
        # Normalize times to start at 0
        window_times = window_times - window_start
        peak_time_normalized = spike['peak_time'] - window_start
        crossing_time_normalized = spike['crossing_time'] - window_start
        
        # Plot
        ax = axes[i]
        ax.plot(window_times, window_pressures, 'b-', linewidth=2)
        
        # Mark peak and crossing
        ax.axvline(x=peak_time_normalized, color='r', linestyle='--', alpha=0.5, label='Peak')
        ax.axvline(x=crossing_time_normalized, color='g', linestyle='--', alpha=0.5, label='Ambient Crossing')
        ax.axhline(y=spike['ambient_pressure'], color='k', linestyle='--', alpha=0.3, 
                  label=f'Ambient ({spike["ambient_pressure"]:.1f} mbar)')
        
        # Calculate annotation position
        x_pos = crossing_time_normalized - (crossing_time_normalized - peak_time_normalized) * 0.3
        y_pos = (spike['peak_pressure'] + spike['ambient_pressure']) / 2
        
        # Add duration annotation with adjusted position and arrow
        ax.annotate(
            f'Duration: {spike["duration"]:.1f} ms\nPeak: {spike["peak_pressure"]:.1f} mbar',
            xy=(peak_time_normalized, spike['peak_pressure']),
            xytext=(x_pos, y_pos),
            bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.5),
            ha='center',
            va='center',
            arrowprops=dict(arrowstyle='->'),
        )
        
        # Set y-axis limits based on spike type
        if spike['type'] == 'high':
            ax.set_ylim(spike['ambient_pressure'] - 20, 1300)
        else:
            ax.set_ylim(spike['ambient_pressure'] - 10, 900)
        
        # Set x-axis ticks every 100ms
        max_time = max(window_times)
        tick_positions = np.arange(0, max_time + 100, 100)  # Add 100 to include the last tick
        ax.set_xticks(tick_positions)
        ax.set_xticklabels([f'{int(x)}' for x in tick_positions])
        
        # Update title to reflect new numbering
        ax.set_title(f'{"High" if spike["type"] == "high" else "Low"} Pressure Spike {i+1}')
        ax.set_xlabel('Time (milliseconds)')
        ax.set_ylabel('Pressure (mbar)')
        ax.grid(True, alpha=0.3)
        ax.legend()

    plt.tight_layout()
    
    # Add input parameters text box
    input_text = f"Analysis Parameters:\nBase Filename: {base_filename}"
    plt.figtext(0.02, 0.02, input_text,
                bbox=dict(facecolor='white', edgecolor='black', alpha=0.8),
                fontsize=10, family='monospace')
    
    output_filename = f"{base_filename}_spike_analysis.png"
    plt.savefig(output_filename, dpi=300, bbox_inches='tight')
    print(f"Plot saved as '{output_filename}'")    
    # Print durations
    print("\nSpike Durations:")
    for i, spike in enumerate(spike_data):
        print(f"{spike['type'].capitalize()} Spike {i+1}:")
        print(f"  Duration: {spike['duration']:.1f} ms")
        print(f"  Peak Pressure: {spike['peak_pressure']:.1f} mbar")
        print(f"  Ambient Pressure: {spike['ambient_pressure']:.1f} mbar")
        print(f"  Peak Time: {spike['peak_time']:.1f} ms")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <base_filename>")
        sys.exit(1)

    base_filename = sys.argv[1]
    times, pressures = process_files(base_filename)
    spike_data = find_spike_durations(times, pressures)
    plot_spikes(times, pressures, spike_data, base_filename)