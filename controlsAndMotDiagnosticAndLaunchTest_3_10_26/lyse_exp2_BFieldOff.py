# multishot_exp2_decay_images.py
# Multishot analysis for Experiment 2: show all decay images with delay times

import numpy as np
import matplotlib.pyplot as plt
import lyse
import h5py
import os

plt.rc('font', family='serif')
plt.rc('xtick', labelsize=14)
plt.rc('ytick', labelsize=14)
plt.rc('axes', titlesize=16, labelsize=16)
plt.rc('legend', fontsize=14)
plt.rc('figure', titlesize=18)

ORIENTATION = 'my_ids_camera'
ROI = (268, 285, 353, 366)

# Get the dataframe of all loaded shots
df = lyse.data()

# Collect decay images and delays from all shots
shots = []
for i in range(len(df)):
    filepath = df['filepath'].iloc[i]
    if not isinstance(filepath, str):
        filepath = str(filepath)
        #print(filepath)
    try:
        with h5py.File(filepath, 'r') as f:
            delay = float(f['globals'].attrs['image_delay'])
            img = np.array(f['images'][ORIENTATION]['decay']['atom'], dtype=float)
            shots.append((delay, img, os.path.basename(filepath)))
    except Exception as e:
        print(f"Skipping {filepath}: {e}")

if len(shots) == 0:
    print("No valid shots found.")
else:
    # Sort by delay time
    shots.sort(key=lambda x: x[0])

    n = len(shots)
    ncols = min(5, n)
    nrows = int(np.ceil(n / ncols))

    r0, r1, c0, c1 = ROI
    pad = 0
    plot_r0 = max(0, r0 - pad)
    plot_r1 = min(shots[0][1].shape[0], r1 + pad)
    plot_c0 = max(0, c0 - pad)
    plot_c1 = min(shots[0][1].shape[1], c1 + pad)

    # Consistent color scale
    vmin = min(s[1].min() for s in shots)
    vmax = max(s[1].max() for s in shots)

    fig, axes = plt.subplots(nrows, ncols, figsize=(4 * ncols, 4 * nrows))
    fig.suptitle('Exp 2: MOT Decay — All Shots')

    if nrows == 1 and ncols == 1:
        axes = np.array([[axes]])
    elif nrows == 1:
        axes = axes[np.newaxis, :]
    elif ncols == 1:
        axes = axes[:, np.newaxis]

    for i, (delay, img, fname) in enumerate(shots):
        r = i // ncols
        c = i % ncols
        ax = axes[r, c]
        ax.imshow(img, vmin=vmin, vmax=vmax, cmap='inferno', origin='lower')
        ax.set_xlim(plot_c0, plot_c1)
        ax.set_ylim(plot_r0, plot_r1)
        ax.set_title(f'Shot {i}\ndelay = {delay*1000:.0f} ms')
        ax.axis('off')

    # Turn off unused panels
    for i in range(n, nrows * ncols):
        r = i // ncols
        c = i % ncols
        axes[r, c].axis('off')

    plt.tight_layout()