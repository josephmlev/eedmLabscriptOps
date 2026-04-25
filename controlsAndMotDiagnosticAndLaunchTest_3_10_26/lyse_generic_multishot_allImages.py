# multishot_all_images.py
# Multishot analysis: show all images from each shot

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
ROI = (570, 590, 790, 810)
gain = 14
pad = 100

# Images to display (set to None to show all)
SHOW_ONLY = None  # e.g. ['molasses_early'] or None for all

# Globals to print per-panel as subplot titles (vary shot to shot)
PRINT_GLOBALS = ['t_camera_delay']  # e.g. ['t_redshift']

# Globals to print once in the figure title (same across shots)
PRINT_GLOBALS_TOP = ['v_stage', 't_dark']  # e.g. ['v_laser_jump_rel', 't_dark']

EXCLUDE_IMAGES = ['reference']  # e.g. ['reference', 'background'] or [] for none

# ── Load all shots ────────────────────────────────────────────────────────────

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

# ── Print globals and ROI sums ────────────────────────────────────────────────

if len(shots) == 0:
    print("No valid shots found.")
else:
    # Print all globals for every shot
    for s in shots:
        print(f"\n{s['basename']}")
        if s['note']:
            print(f"  note: {s['note']}")
        for key, val in s['globals'].items():
            print(f"  {key}: {val}")

    # Print ROI sums
    r0, r1, c0, c1 = ROI
    print("\nROI brightness sums:")
    for s in shots:
        for j, img in enumerate(s['images']):
            name = s['image_names'][j]
            if (SHOW_ONLY is None or name in SHOW_ONLY) and name not in EXCLUDE_IMAGES:
                roi_sum = img[r0:r1, c0:c1].sum()
                # Build a label from PRINT_GLOBALS if defined
                extras = '  '.join(
                    f"{k}: {s['globals'].get(k, '?')}"
                    for k in PRINT_GLOBALS
                )
                print(f"  {s['basename']} | {name}"
                      + (f" | {extras}" if extras else "")
                      + f" | ROI sum: {roi_sum:.0f}")

    # ── Build panel list ──────────────────────────────────────────────────────

    panels = []
    for s in shots:
        for j, img in enumerate(s['images']):
            name = s['image_names'][j]
            if (SHOW_ONLY is None or name in SHOW_ONLY) and name not in EXCLUDE_IMAGES:
                panels.append({
                    'img': img,
                    'label': name,
                    'shot': s['basename'],
                    'globals': s['globals'],
                })

    if len(panels) == 0:
        print("No panels matched SHOW_ONLY filter.")
    else:
        # ── Plot setup ────────────────────────────────────────────────────────

        n = len(panels)
        ncols = 3#min(5, n)
        nrows = 2#int(np.ceil(n / ncols))


        plot_r0 = max(0, r0 - pad)
        plot_r1 = min(panels[0]['img'].shape[0], r1 + pad)
        plot_c0 = max(0, c0 - pad)
        plot_c1 = min(panels[0]['img'].shape[1], c1 + pad)

        vmin = min(p['img'].min() for p in panels)
        vmax = max(p['img'].max() for p in panels)

        fig, axes = plt.subplots(nrows, ncols, figsize=(4 * ncols, 4 * nrows))

        # Figure title: directory + shared globals
        shot_dir = os.path.dirname(shots[0]['filepath'])
        top_info = '  '.join(
            f"{k}: {shots[0]['globals'][k]}"
            for k in PRINT_GLOBALS_TOP
            if k in shots[0]['globals']
        )
        fig.suptitle(
            f"All images\n{shot_dir}"
            + (f"\n{top_info}" if top_info else ""),
            fontsize=12
        )

        if nrows == 1 and ncols == 1:
            axes = np.array([[axes]])
        elif nrows == 1:
            axes = axes[np.newaxis, :]
        elif ncols == 1:
            axes = axes[:, np.newaxis]

        # ── Draw panels ───────────────────────────────────────────────────────

        for i, p in enumerate(panels):
            row = i // ncols
            col = i % ncols
            ax = axes[row, col]

            crop = p['img'][plot_r0:plot_r1, plot_c0:plot_c1]
            ax.imshow(crop * gain, vmin=vmin, vmax=vmax, cmap='inferno')

            roi_rect = Rectangle(
                (c0 - plot_c0, r0 - plot_r0), c1 - c0, r1 - r0,
                linewidth=1, edgecolor='cyan', facecolor='none', linestyle='--'
            )
            ax.add_patch(roi_rect)

            roi_sum = p['img'][r0:r1, c0:c1].sum()
            title = f"{p['shot']}\n{p['label']}\nROI sum: {roi_sum:.0f}"
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

        # Hide unused axes
        for i in range(n, nrows * ncols):
            axes[i // ncols, i % ncols].axis('off')

        plt.tight_layout()