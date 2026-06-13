import h5py
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import scipy.signal

filepath = Path(r"C:\Experiments\eedmLabscriptOps\exp11_switchArmsAndLaunch\2026\05\07\0004\2026-05-07_0004_exp11_switchArmsAndLaunch_0.h5")

if not filepath.exists():
    raise FileNotFoundError(f"Could not find: {filepath}")

trace_name = 'data/traces/MRR_position'

with h5py.File(filepath, 'r') as f:
    mrr_data = f[trace_name][()]

t = mrr_data['t']
values = mrr_data['values']

position_mm = values * (300.0 / 5.0)
position_mm = scipy.signal.savgol_filter(position_mm, window_length=500, polyorder=3)
# Moving box mean filter
window = 151  # adjust as needed (must be odd to keep alignment clean)
kernel = np.ones(window) / window
position_mm = np.convolve(position_mm, kernel, mode='same')

# Pick a window in the middle where motion is at constant velocity
N = len(t)
i1 = N // 2 - N // 10
i2 = N // 2 + N // 10 -5000

dt_mean = np.mean(np.diff(t[i1:i2]))
dt_first = t[i1+1] - t[i1]

print(f"N samples total: {N}")
print(f"Window indices: {i1} to {i2}")
print(f"t[i1]={t[i1]}, t[i2]={t[i2]}")
print(f"dt (mean in window) = {dt_mean}")
print(f"dt (first in window) = {dt_first}")
print(f"Window t span: {t[i2]-t[i1]} s")
print(f"Window position span: {position_mm[i2]-position_mm[i1]} mm")
print(f"Naive velocity in window: {(position_mm[i2]-position_mm[i1])/(t[i2]-t[i1])} mm/s")

# Also check for any weirdness in dt
dts = np.diff(t)
print(f"\ndt min/max/std: {dts.min()}, {dts.max()}, {dts.std()}")
print(f"Any duplicate t? {(dts == 0).any()}")


plt.figure(figsize=(10, 5))
plt.plot(t, values, lw=0.8)
plt.xlabel('Time (s)')
plt.ylabel('Voltage (V)')
plt.title('MRR_position trace')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()

plt.figure(figsize=(10, 5))
plt.plot(t, position_mm, lw=0.8)
plt.xlabel('Time (s)')
plt.ylabel('position (mm)')
plt.title('MRR_position trace')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()

# Convert voltage (0-5V) to position (0-300mm)
# Velocity in mm/s via central differences
velocity = np.gradient(position_mm, t)

plt.figure(figsize=(10, 5))
plt.plot(t, velocity, lw=0.8)
plt.xlabel('Time (s)')
plt.ylabel('Velocity (mm/s)')
plt.title('MRR velocity')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()

