import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from collections import defaultdict

# ---- YOU ADAPT THESE TWO ----
def parse_drop_time(path):
    """Return drop time in ms from a filename/path."""
    import re
    m = re.search(r'([\d.]+)ms', Path(path).name)
    return float(m.group(1))

def load_od(path):
    """Return the OD image (2D ndarray) for one shot."""
    return np.load(path)   # or h5py / fits / raw-frame processing
# ------------------------------

def fit_shot(od, roi=None):
    """Call your existing 2D Gaussian fitter.
    Return dict with keys: offset, amp, x0, y0, sigma_x, sigma_y,
    integrated, and *_err versions."""
    return your_gaussian_fit(od, roi=roi)   # <-- plug in your fitter

def run_multishot(folder, pattern='*.npy', roi=None):
    files = sorted(Path(folder).glob(pattern))
    results = defaultdict(list)   # drop_time -> list of fit dicts

    for f in files:
        try:
            t = parse_drop_time(f)
            fit = fit_shot(load_od(f), roi=roi)
            fit['file'] = f.name
            results[t].append(fit)
        except Exception as e:
            print(f"skip {f.name}: {e}")

    return dict(sorted(results.items()))

def plot_vs_droptime(results, keys=('sigma_x','sigma_y','amp',
                                    'integrated','x0','y0')):
    times = np.array(list(results.keys()))
    n = len(keys)
    fig, axes = plt.subplots((n+1)//2, 2, figsize=(11, 3*((n+1)//2)))
    axes = np.ravel(axes)

    for ax, key in zip(axes, keys):
        for t in times:
            vals = [s[key] for s in results[t]]
            errs = [s.get(key+'_err', 0) for s in results[t]]
            # individual shots (faint)
            ax.errorbar([t]*len(vals), vals, yerr=errs, fmt='.',
                        alpha=0.35, color='gray', zorder=1)
        # per-time mean +/- std across shots
        means = [np.mean([s[key] for s in results[t]]) for t in times]
        stds  = [np.std ([s[key] for s in results[t]]) for t in times]
        ax.errorbar(times, means, yerr=stds, fmt='o-', capsize=3,
                    color='C0', zorder=2)
        ax.set_xlabel('drop time (ms)')
        ax.set_ylabel(key)
    for ax in axes[n:]:
        ax.axis('off')
    fig.tight_layout()
    return fig

if __name__ == '__main__':
    res = run_multishot('data/tof_run1', pattern='*.npy',
                        roi=(slice(600,1000), slice(650,1000)))
    fig = plot_vs_droptime(res)
    plt.show()