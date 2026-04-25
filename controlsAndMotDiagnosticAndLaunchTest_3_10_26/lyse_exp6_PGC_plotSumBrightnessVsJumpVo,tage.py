# multishot_exp_pgc_roi_vs_jump.py
# Multishot analysis: plot ROI brightness sum vs v_laser_jump_rel

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
ROI = (280, 310, 375, 395)
SHOW_ONLY = ['molasses_late']

df = lyse.data()

v_jumps = []
roi_sums = []

for i in range(len(df)):
    filepath = df['filepath'].iloc[i]
    if not isinstance(filepath, str):
        filepath = str(filepath)
    try:
        with h5py.File(filepath, 'r') as f:
            v_jump = float(f['globals'].attrs['v_laser_jump_rel'])

            if ORIENTATION in f['images']:
                for group_name in f['images'][ORIENTATION]:
                    if group_name in SHOW_ONLY:
                        grp = f['images'][ORIENTATION][group_name]
                        if 'atom' in grp:
                            img = np.array(grp['atom'], dtype=float)
                            r0, r1, c0, c1 = ROI
                            roi_sum = img[r0:r1, c0:c1].sum()
                            v_jumps.append(v_jump)
                            roi_sums.append(roi_sum)
                            print(f"  {os.path.basename(filepath)} | {group_name} | v_laser_jump_rel: {v_jump} | ROI sum: {roi_sum:.0f}")
    except Exception as e:
        print(f"Skipping {filepath}: {e}")

if len(v_jumps) == 0:
    print("No valid data found.")
else:
    v_jumps = np.array(v_jumps)
    roi_sums = np.array(roi_sums)

    # Sort by v_laser_jump_rel
    sort_idx = np.argsort(v_jumps)
    v_jumps = v_jumps[sort_idx]
    roi_sums = roi_sums[sort_idx]

    shot_dir = os.path.dirname(df['filepath'].iloc[0])

    fig, ax = plt.subplots(figsize=(8, 5))
    fig.suptitle(f'ROI brightness vs v_laser_jump_rel\n{shot_dir}', fontsize=12)

    ax.plot(v_jumps, roi_sums, 'ko-', markersize=8)
    ax.set_xlabel('v_laser_jump_rel (V)')
    ax.set_ylabel('ROI sum (counts)')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()