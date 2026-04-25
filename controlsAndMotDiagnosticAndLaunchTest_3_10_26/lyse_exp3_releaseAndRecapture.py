# multishot_exp3a_qualitative.py
# Multishot analysis for Experiment 3A: show reference and recapture images side by side

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

# Collect reference and recapture images with t_dark from all shots
shots = []
for i in range(len(df)):
    filepath = df['filepath'].iloc[i]
    if not isinstance(filepath, str):
        filepath = str(filepath)
    try:
        with h5py.File(filepath, 'r') as f:
            t_dark = float(f['globals'].attrs['t_dark'])
            ref_img = np.array(f['images'][ORIENTATION]['reference']['atom'], dtype=float)
            recap_img = np.array(f['images'][ORIENTATION]['recapture']['atom'], dtype=float)
            shots.append((t_dark, ref_img, recap_img, os.path.basename(filepath)))
    except Exception as e:
        print(f"Skipping {filepath}: {e}")

if len(shots) == 0:
    print("No valid shots found.")
else:
    # Sort by dark time
    shots.sort(key=lambda x: x[0])

    n = len(shots)

    r0, r1, c0, c1 = ROI
    pad = 60
    plot_r0 = max(0, r0 - pad)
    plot_r1 = min(shots[0][1].shape[0], r1 + pad)
    plot_c0 = max(0, c0 - pad)
    plot_c1 = min(shots[0][1].shape[1], c1 + pad)

    # Consistent color scale across all images
    all_imgs = [s[1] for s in shots] + [s[2] for s in shots]
    vmin = min(img.min() for img in all_imgs)
    vmax = max(img.max() for img in all_imgs)

    # Grid layout: each shot takes 2 columns (ref + recapture)
    ncols = min(5, n)
    nrows = int(np.ceil(n / ncols))

    fig, axes = plt.subplots(nrows, ncols * 2, figsize=(4 * ncols, 4 * nrows))
    shot_folder = os.path.dirname(shots[0][3]) if os.path.dirname(shots[0][3]) else os.path.dirname(df['filepath'].iloc[0])
    note = 'Turn off MRR shutter and MOT coils, wait t_dark, open shutter, leave coils off. Wait 1000 ms after opening shutter before imaging.'

    shot_folder = os.path.dirname(shots[0][3]) if os.path.dirname(shots[0][3]) else os.path.dirname(df['filepath'].iloc[0])
    fig.suptitle(f'Exp 3A: Release and Recapture\n{shot_folder}\n{note}', fontsize=14)

    # Ensure axes is always 2D
    if nrows == 1 and ncols * 2 == 1:
        axes = np.array([[axes]])
    elif nrows == 1:
        axes = axes[np.newaxis, :]
    elif ncols * 2 == 1:
        axes = axes[:, np.newaxis]

    for i, (t_dark, ref_img, recap_img, fname) in enumerate(shots):
        r = i // ncols
        c = i % ncols

        # Reference image
        ax_ref = axes[r, c * 2]
        ax_ref.imshow(ref_img, vmin=vmin, vmax=vmax, cmap='inferno', origin='lower')
        ax_ref.set_xlim(plot_c0, plot_c1)
        ax_ref.set_ylim(plot_r0, plot_r1)
        ax_ref.set_title(f'Ref: t_dark = {t_dark*1000:.1f} ms', fontsize=9)
        ax_ref.axis('off')

        # Recapture image
        ax_recap = axes[r, c * 2 + 1]
        ax_recap.imshow(recap_img, vmin=vmin, vmax=vmax, cmap='inferno', origin='lower')
        ax_recap.set_xlim(plot_c0, plot_c1)
        ax_recap.set_ylim(plot_r0, plot_r1)
        ax_recap.set_title(f'Recap: t_dark = {t_dark*1000:.1f} ms', fontsize=9)
        ax_recap.axis('off')

    # Turn off unused panels
    for i in range(n, nrows * ncols):
        r = i // ncols
        c = i % ncols
        axes[r, c * 2].axis('off')
        axes[r, c * 2 + 1].axis('off')

    plt.tight_layout()