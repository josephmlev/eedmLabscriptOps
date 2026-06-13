# singleshot_photoncounts.py
# Single-shot analysis: plot cumulative photon counts and per-sample diffs

import numpy as np
import matplotlib.pyplot as plt
import lyse
import h5py

with h5py.File(lyse.path, 'r') as f:
    data = np.array(f['data/traces/photon_counts'])

# The trace is an array with a time column and a cumulative counts column
t = data['t']
cumulative = data['values']

# Difference: how much counts went up since the previous sample
diff = np.diff(cumulative, prepend=cumulative[0])

fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, figsize=(8, 6))

ax1.plot(t, cumulative)
ax1.set_ylabel('Cumulative counts')

ax2.plot(t, diff)
ax2.set_ylabel('Counts per sample')
ax2.set_xlabel('Time (s)')

plt.tight_layout()