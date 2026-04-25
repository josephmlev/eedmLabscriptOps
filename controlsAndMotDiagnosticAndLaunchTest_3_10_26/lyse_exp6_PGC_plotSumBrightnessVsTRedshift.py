# multishot_exp_pgc_roi_vs_tredshift.py
# Multishot analysis: plot ROI brightness sum vs t_redshift

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

t_redshifts = []
roi_sums = []

for i in range(len(df)):
    filepath = df['filepath'].iloc[i]
    if not isinstance(filepath, str):
        filepath = str(filepath)
    try:
        with h5py.File(filepath, 'r') as f:
            t_rs = float(f['globals'].attrs['t_redshift'])

            if ORIENTATION in f['images']:
                for group_name in f['images'][ORIENTATION]:
                    if group_name in SHOW_ONLY:
                        grp = f['images'][ORIENTATION][group_name]
                        if 'atom' in grp:
                            img = np.array(grp['atom'], dtype=float)
                            r0, r1, c0, c1 = ROI
                            roi_sum = img[r0:r1, c0:c1].sum()
                            t_redshifts.append(t_rs)
                            roi_sums.append(roi_sum)
                            print(f"  {os.path.basename(filepath)} | {group_name} | t_redshift: {t_rs} | ROI sum: {roi_sum:.0f}")
    except Exception as e:
        print(f"Skipping {filepath}: {e}")

if len(t_redshifts) == 0:
    print("No valid data found.")
else:
    t_redshifts = np.array(t_redshifts)
    roi_sums = np.array(roi_sums)

    sort_idx = np.argsort(t_redshifts)
    t_redshifts = t_redshifts[sort_idx]
    roi_sums = roi_sums[sort_idx]

    shot_dir = os.path.dirname(df['filepath'].iloc[0])

    fig, ax = plt.subplots(figsize=(8, 5))
    fig.suptitle(f'ROI brightness vs t_redshift\n{shot_dir}', fontsize=12)

    ax.plot(t_redshifts * 1000, roi_sums, 'ko-', markersize=8)
    ax.set_xlabel('t_redshift (ms)')
    ax.set_ylabel('ROI sum (counts)')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()