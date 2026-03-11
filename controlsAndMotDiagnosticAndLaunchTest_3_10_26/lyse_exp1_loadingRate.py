# analysis_loading.py
# Lyse single-shot analysis for Experiment 1: Loading Rate & Atom Number
#
# Shows: background image, a few loading snapshots, steady-state with ROI box,
#        and a loading curve with exponential fit.

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from scipy.optimize import curve_fit
import lyse
import h5py
import os

shot_file = os.path.basename(lyse.path)

plt.rc('font', family='serif')
plt.rc('xtick', labelsize=18)
plt.rc('ytick', labelsize=18)
plt.rc('axes', titlesize=20, labelsize=16)
plt.rc('legend', fontsize=18)
plt.rc('figure', titlesize=18)

# ============================================================
# USER PARAMETERS — adjust these to your setup
# ============================================================
# ROI in pixel coordinates (row_start, row_end, col_start, col_end)
#ROI = (275, 295, 348, 365) #from 2026 Mar 10
ROI = (268, 285, 353, 366)

# Image orientation / device name in HDF5
ORIENTATION = 'my_ids_camera'

# How many loading snapshots to show (evenly spaced from the series)
N_SNAPSHOTS = 100

# ============================================================
# Model
# ============================================================
def loading_curve(t, N_ss, tau, t0):
    """Exponential rise: N(t) = N_ss * (1 - exp(-(t - t0) / tau))"""
    return N_ss * (1.0 - np.exp(-(t - t0) / tau))


# ============================================================
# Load data
# ============================================================
run = lyse.Run(lyse.path)

with h5py.File(lyse.path, 'r') as f:
    IMAGE_INTERVAL = float(f['globals'].attrs['image_interval'])
    image_group = f['images'][ORIENTATION]  

    # Background
    bg = np.array(image_group['background']['atom'], dtype=float)

    # Loading images — sort by name to get time ordering
    loading_keys = sorted([k for k in image_group.keys() if k.startswith('loading_')])
    loading_imgs = []
    for key in loading_keys:
        loading_imgs.append(np.array(image_group[key]['atom'], dtype=float))

    # Steady state
    ss_img = np.array(image_group['steady_state']['atom'], dtype=float)


# ============================================================
# Compute fluorescence vs time
# ============================================================
r0, r1, c0, c1 = ROI
print(f"Number of loading images: {len(loading_imgs)}")
print(f"First loading image shape: {loading_imgs[0].shape}")
print(f"ROI: ({r0}, {r1}, {c0}, {c1})")
roi_data = ss_img[r0:r1, c0:c1]
print(f"ROI stats — min: {roi_data.min():.0f}, max: {roi_data.max():.0f}, mean: {roi_data.mean():.1f}")
bg_counts = loading_imgs[0][r0:r1, c0:c1].sum()  # use first loading image for background counts since it is mostly background flourescence

counts = []
times = []
for i, img in enumerate(loading_imgs):
    counts.append(img[r0:r1, c0:c1].sum() - bg_counts)
    times.append(i * IMAGE_INTERVAL)

counts = np.array(counts)
times = np.array(times)

ss_counts = ss_img[r0:r1, c0:c1].sum() - bg_counts


# ============================================================
# Fit
# ============================================================
try:
    p0 = [ss_counts, 1.0, 0.0]
    bounds = ([0, 0.01, -2.0], [ss_counts * 3, 30.0, 2.0])
    popt, pcov = curve_fit(loading_curve, times, counts, p0=p0, bounds=bounds)
    N_ss_fit, tau_fit, t0_fit = popt
    perr = np.sqrt(np.diag(pcov))
    fit_success = True
except Exception as e:
    print(f"Fit failed: {e}")
    fit_success = False

# ============================================================
# Save results
# ============================================================
if fit_success:
    run.save_result('loading_tau', tau_fit)
    run.save_result('loading_tau_err', perr[1])
    run.save_result('loading_N_ss', N_ss_fit)
    run.save_result('loading_N_ss_err', perr[0])
    run.save_result('steady_state_counts', ss_counts)
    print(f"Loading time constant: {tau_fit:.3f} ± {perr[1]:.3f} s")
    print(f"Steady-state counts:   {N_ss_fit:.0f} ± {perr[0]:.0f}")

# ============================================================
# Pick which loading snapshots to display
# ============================================================
n_total = len(loading_imgs)
n_display = min(3, n_total)
if n_total <= 3:
    snap_indices = list(range(n_total))
else:
    # Need fit first, so move snapshot selection after the fit
    if fit_success:
        t_max = 2 * tau_fit
        i_max = min(int(t_max / IMAGE_INTERVAL), n_total - 1)
    else:
        i_max = n_total - 1
    log_indices = np.logspace(0, np.log10(max(i_max, 1)), 3).astype(int)
    snap_indices = sorted(set(np.clip(log_indices, 0, n_total - 1)))

# ============================================================
# Figure
# ============================================================
n_image_panels = 2 + len(snap_indices)  # background + snapshots + steady state
fig = plt.figure(figsize=(14, 8))
fig.suptitle(shot_file.replace('.h5', ''), fontsize=18)

# Use gridspec: top row for images, bottom row for the loading curve
gs = fig.add_gridspec(2, n_image_panels, height_ratios=[1, 1.2], hspace=0.35, wspace=0.3)

# Consistent color scale across all images
all_imgs = [bg] + [loading_imgs[i] for i in snap_indices] + [ss_img]
vmin = min(img.min() for img in all_imgs)
vmax = max(img.max() for img in all_imgs)

#zoom into a pad region around the ROI
pad = 10
plot_r0 = max(0, r0 - pad)
plot_r1 = min(ss_img.shape[0], r1 + pad)
plot_c0 = max(0, c0 - pad)
plot_c1 = min(ss_img.shape[1], c1 + pad)

# --- Top row: images ---
# Background
ax = fig.add_subplot(gs[0, 0])
ax.imshow(bg, vmin=vmin, vmax=vmax, cmap='inferno', origin='lower')
ax.set_xlim(plot_c0, plot_c1)
ax.set_ylim(plot_r0, plot_r1)
ax.set_title('Background')
ax.axis('off')

# Loading snapshots
for panel_i, img_i in enumerate(snap_indices):
    ax = fig.add_subplot(gs[0, panel_i + 1])
    ax.imshow(loading_imgs[img_i], vmin=vmin, vmax=vmax, cmap='inferno', origin='lower')
    ax.set_xlim(plot_c0, plot_c1)
    ax.set_ylim(plot_r0, plot_r1)
    ax.set_title(f't = {img_i * IMAGE_INTERVAL:.2f} s')
    ax.axis('off')

# Steady state with ROI box
ax_ss = fig.add_subplot(gs[0, -1])
ax_ss.imshow(ss_img, vmin=vmin, vmax=vmax, cmap='inferno', origin='lower')
ax_ss.set_xlim(plot_c0, plot_c1)
ax_ss.set_ylim(plot_r0, plot_r1)
roi_rect = Rectangle(
    (c0, r0), c1 - c0, r1 - r0,
    linewidth=.5, edgecolor='cyan', facecolor='none', linestyle='--'
)
ax_ss.add_patch(roi_rect)
#ax_ss.set_title('Steady state')
roi_data = ss_img[r0:r1, c0:c1]
ax_ss.set_title(f'Steady state\nROI min:{roi_data.min():.0f} max:{roi_data.max():.0f} mean:{roi_data.mean():.1f}')
ax_ss.axis('off')

# --- Bottom row: loading curve spanning all columns ---
ax_plot = fig.add_subplot(gs[1, :])
ax_plot.plot(times, counts, 'ko', markersize=5, label='Data')
ax_plot.axhline(ss_counts, color='gray', linestyle=':', alpha=0.5, label=f'Measured SS at t_f + 2 sec. \n= {ss_counts:.0f} counts')

if fit_success:
    t_fit = np.linspace(times[0], times[-1], 300)
    ax_plot.plot(t_fit, loading_curve(t_fit, *popt), 'r-', linewidth=2,
                 label=f'Fit: A*(1 - exp(-t/tau))\n'
                       f'A = {N_ss_fit:.0f} +- {perr[0]:.0f} counts\n'
                       f'tau = {round(tau_fit*1000,2)} +- {round(perr[1]*1000,2)} ms')

ax_plot.set_xlabel('Time since shutter open (s)')
ax_plot.set_ylabel('Fluorescence (background-subtracted counts)')
ax_plot.set_title('MOT Loading Curve')
ax_plot.legend(loc='lower right')
ax_plot.set_xlim(left=-0.1)
ax_plot.set_ylim(bottom=0)
ax_plot.grid(True, alpha=0.3)

plt.savefig('loading_analysis.png', dpi=150, bbox_inches='tight')
#plt.show()