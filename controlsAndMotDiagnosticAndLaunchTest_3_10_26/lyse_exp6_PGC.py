# multishot_exp_pgc_all_images.py
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
ROI = (280, 305, 375, 395)

df = lyse.data()

SHOW_ONLY = ['molasses_early']
PRINT_GLOBALS = [ 't_redshift'] #these are changed shot to shot and label each plot
PRINT_GLOBALS_TOP = [' v_laser_jump_rel, t_dark'] #these are the same between shots and only need to be printed once at the top

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
                        image_names.append(group_name)
                        images.append(np.array(grp['atom'], dtype=float))

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
                v_jump = s['globals'].get('v_laser_jump_rel', '?')
                print(f"  {s['basename']} | {s['image_names'][j]} | v_laser_jump_rel: {v_jump} | ROI sum: {roi_sum:.0f}")
    # Flatten all images into one list for a simple grid
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

    n = len(panels)
    ncols = min(5, n)
    nrows = int(np.ceil(n / ncols))

    r0, r1, c0, c1 = ROI
    pad = 20
    plot_r0 = max(0, r0 - pad)
    plot_r1 = min(panels[0]['img'].shape[0], r1 + pad)
    plot_c0 = max(0, c0 - pad)
    plot_c1 = min(panels[0]['img'].shape[1], c1 + pad)

    vmin = min(p['img'].min() for p in panels)
    vmax = max(p['img'].max() for p in panels)

    fig, axes = plt.subplots(nrows, ncols, figsize=(4 * ncols, 4 * nrows))

    shot_dir = os.path.dirname(shots[0]['filepath'])
    shot_dir = os.path.dirname(shots[0]['filepath'])
    top_info = ''
    for key in PRINT_GLOBALS_TOP:
        if key in shots[0]['globals']:
            top_info += f"{key}: {shots[0]['globals'][key]}  "
    fig.suptitle(f'All images\n{shot_dir}\n{top_info}', fontsize=12)
    
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

        # Find center of mass within padded ROI, thresholded to isolate cloud
        crop_for_cm = p['img'][plot_r0:plot_r1, plot_c0:plot_c1].copy()
        threshold = crop_for_cm.mean() + 2 * crop_for_cm.std()
        crop_for_cm[crop_for_cm < threshold] = 0
        total = crop_for_cm.sum()
        if total > 0:
            rows_idx = np.arange(crop_for_cm.shape[0])
            cols_idx = np.arange(crop_for_cm.shape[1])
            cm_r = (crop_for_cm.sum(axis=1) * rows_idx).sum() / total
            cm_c = (crop_for_cm.sum(axis=0) * cols_idx).sum() / total
            #ax.plot(cm_c, cm_r, 'w*', markersize=12)
            cm_r_full = cm_r + plot_r0
            cm_c_full = cm_c + plot_c0
            #ax.plot(cm_c, cm_r, 'w*', markersize=12)
            print(f"  {p['shot']} | {p['label']} | CM row: {cm_r_full:.1f} | CM col: {cm_c_full:.1f}")

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