# multishot_exp_pgc_select_images.py
# Multishot analysis: show selected images from each shot

import numpy as np
import matplotlib.pyplot as plt
import lyse
import h5py
import os
from matplotlib.patches import Rectangle

plt.rc('font', family='serif')
plt.rc('xtick', labelsize=14)
plt.rc('ytick', labelsize=14)
plt.rc('axes', titlesize=16, labelsize=16)
plt.rc('legend', fontsize=14)
plt.rc('figure', titlesize=18)

ORIENTATION = 'my_ids_camera'
ROI = (260, 290, 375, 395)
SHOW_ONLY = ['molasses_late']
PRINT_GLOBALS = ['v_stage']
PRINT_GLOBALS_TOP = ['t_hold']

df = lyse.data()

shots = []
for i in range(len(df)):
    filepath = df['filepath'].iloc[i]
    if not isinstance(filepath, str):
        filepath = str(filepath)
    try:
        with h5py.File(filepath, 'r') as f:
            note = ''
            if 'note' in f['globals'].attrs:
                note = str(f['globals'].attrs['note'])

            globals_dict = {}
            for key in f['globals'].attrs:
                globals_dict[key] = f['globals'].attrs[key]

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

            if len(images) > 0:
                shots.append({
                    'filepath': filepath,
                    'basename': os.path.basename(filepath),
                    'note': note,
                    'globals': globals_dict,
                    'image_names': image_names,
                    'images': images,
                })
    except Exception as e:
        print(f"Skipping {filepath}: {e}")

if len(shots) == 0:
    print("No valid shots found.")
else:
    # Print notes and globals for each shot
    for s in shots:
        print(f"\n{s['basename']}")
        if s['note']:
            print(f"  note: {s['note']}")
        for key, val in s['globals'].items():
            print(f"  {key}: {val}")

    # Print ROI sum for each shot
    r0, r1, c0, c1 = ROI
    print("\nROI brightness sums:")
    for s in shots:
        for j, img in enumerate(s['images']):
            if s['image_names'][j] in SHOW_ONLY:
                roi_sum = img[r0:r1, c0:c1].sum()
                print(f"  {s['basename']} | {s['image_names'][j]} | ROI sum: {roi_sum:.0f}")

    # Flatten selected images into panels
    panels = []
    for s in shots:
        for j, img in enumerate(s['images']):
            if s['image_names'][j] in SHOW_ONLY:
                panels.append({
                    'img': img,
                    'label': s['image_names'][j],
                    'shot': s['basename'],
                    'globals': s['globals'],
                })

    if len(panels) == 0:
        print("No matching images found for SHOW_ONLY list.")
    else:
        n = len(panels)
        ncols = min(5, n)
        nrows = int(np.ceil(n / ncols))

        pad = 35
        plot_r0 = max(0, r0 - pad)
        plot_r1 = min(panels[0]['img'].shape[0], r1 + pad)
        plot_c0 = max(0, c0 - pad)
        plot_c1 = min(panels[0]['img'].shape[1], c1 + pad)

        vmin = min(p['img'].min() for p in panels)
        vmax = max(p['img'].max() for p in panels)

        fig, axes = plt.subplots(nrows, ncols, figsize=(4 * ncols, 4 * nrows))

        shot_dir = os.path.dirname(shots[0]['filepath'])
        top_info = ''
        for key in PRINT_GLOBALS_TOP:
            if key in shots[0]['globals']:
                val = shots[0]['globals'][key]
                try:
                    val = round(float(val), 4)
                except (ValueError, TypeError):
                    pass
                top_info += f"{key}: {val}  "
        fig.suptitle(f'Selected images\n{shot_dir}\n{top_info}', fontsize=12)

        if nrows == 1 and ncols == 1:
            axes = np.array([[axes]])
        elif nrows == 1:
            axes = axes[np.newaxis, :]
        elif ncols == 1:
            axes = axes[:, np.newaxis]

        for i, p in enumerate(panels):
            r = i // ncols
            c = i % ncols
            ax = axes[r, c]
            crop = p['img'][plot_r0:plot_r1, plot_c0:plot_c1]
            ax.imshow(crop, vmin=vmin, vmax=vmax, cmap='inferno')

            roi_rect = Rectangle(
                (c0 - plot_c0, r0 - plot_r0), c1 - c0, r1 - r0,
                linewidth=1, edgecolor='cyan', facecolor='none', linestyle='--'
            )
            ax.add_patch(roi_rect)

            title = f"{p['shot']}\n{p['label']}"
            for key in PRINT_GLOBALS:
                if key in p['globals']:
                    val = p['globals'][key]
                    try:
                        val = round(float(val), 4)
                    except (ValueError, TypeError):
                        pass
                    title += f"\n{key}: {val}"
            ax.set_title(title, fontsize=9)
            ax.axis('off')

        for i in range(n, nrows * ncols):
            r = i // ncols
            c = i % ncols
            axes[r, c].axis('off')

        plt.tight_layout()