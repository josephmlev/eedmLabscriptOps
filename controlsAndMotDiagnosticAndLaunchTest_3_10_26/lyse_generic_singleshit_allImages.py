# singleshot_all_images.py
# Single-shot analysis: show all images in the shot

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
ROI = (510, 565, 780, 810)
gain = 14

shot_file = os.path.basename(lyse.path)

with h5py.File(lyse.path, 'r') as f:
    # Read note if it exists
    note = ''
    if 'note' in f['globals'].attrs:
        note = str(f['globals'].attrs['note'])

    # Read all globals
    globals_dict = {}
    for key in f['globals'].attrs:
        globals_dict[key] = f['globals'].attrs[key]

    # Read all images
    image_names = []
    images = []
    if ORIENTATION in f['images']:
        for group_name in f['images'][ORIENTATION]:
            grp = f['images'][ORIENTATION][group_name]
            if 'atom' in grp:
                img = np.array(grp['atom'], dtype=float)
                if img.ndim == 2:
                    image_names.append(group_name)
                    images.append(img)

if len(images) == 0:
    print("No valid images found.")
else:
    # Print info
    print(f"\n{shot_file}")
    if note:
        print(f"  note: {note}")
    for key, val in globals_dict.items():
        print(f"  {key}: {val}")

    # ROI sum for each image
    r0, r1, c0, c1 = ROI
    print("\nROI sums:")
    for j, img in enumerate(images):
        roi_sum = img[r0:r1, c0:c1].sum()
        print(f"  {image_names[j]}: {roi_sum:.0f}")

    # Plot
    n = len(images)
    ncols = min(5, n)
    nrows = int(np.ceil(n / ncols))

    pad = 100

    plot_r0 = max(0, r0 - pad)
    plot_r1 = min(images[0].shape[0], r1 + pad)
    plot_c0 = max(0, c0 - pad)
    plot_c1 = min(images[0].shape[1], c1 + pad)

    vmin = min(img.min() for img in images)
    vmax = max(img.max() for img in images)

    fig, axes = plt.subplots(nrows, ncols, figsize=(4 * ncols, 4 * nrows))

    fig.suptitle(shot_file.replace('.h5', ''), fontsize=12)

    if nrows == 1 and ncols == 1:
        axes = np.array([[axes]])
    elif nrows == 1:
        axes = axes[np.newaxis, :]
    elif ncols == 1:
        axes = axes[:, np.newaxis]

    from matplotlib.patches import Rectangle

    for i, img in enumerate(images):
        r = i // ncols
        c = i % ncols
        ax = axes[r, c]
        crop = img[plot_r0:plot_r1, plot_c0:plot_c1]
        ax.imshow(crop*gain, vmin=vmin, vmax=vmax, cmap='inferno')

        roi_rect = Rectangle(
            (c0 - plot_c0, r0 - plot_r0), c1 - c0, r1 - r0,
            linewidth=1, edgecolor='cyan', facecolor='none', linestyle='--'
        )
        ax.add_patch(roi_rect)

        roi_sum = img[r0:r1, c0:c1].sum()
        ax.set_title(f"{image_names[i]}\nROI sum: {roi_sum:.0f}", fontsize=9)
        ax.axis('off')

    for i in range(n, nrows * ncols):
        r = i // ncols
        c = i % ncols
        axes[r, c].axis('off')

    plt.tight_layout()