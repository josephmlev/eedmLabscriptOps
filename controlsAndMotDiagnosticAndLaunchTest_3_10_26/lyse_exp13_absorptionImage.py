# singleshot_all_images.py
# Single-shot analysis: show all images in the shot,
# identify the four named frames, and compute the absorption OD.

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy.optimize import curve_fit
import lyse
import h5py
import os

plt.rc('font', family='serif')
plt.rc('xtick', labelsize=22)
plt.rc('ytick', labelsize=22)
plt.rc('axes', titlesize=26, labelsize=16)
plt.rc('legend', fontsize=14)
plt.rc('figure', titlesize=30)

ORIENTATION = 'my_ids_camera'
ROI = (560, 610, 780, 810)
#ROI = (575, 620, 770, 825)

ROI = (450, 510, 640, 710)
ROI = (0, 1080, 0, 1440)

#ROI = (410, 580, 560, 730)

gain = 1
gain_florescence = 200
pad = 20
slice_x_offset = 3
slice_y_offset = 3

# --- Slice colors (x and y kept distinct for easy visual ID) ---
X_COLOR = 'red'          # x-slice (row cut -> OD vs column)
Y_COLOR = 'deepskyblue'  # y-slice (column cut -> OD vs row)

# --- Image name flags (must match the labscript expose names) ---
FLUOR_REF_NAME   = 'florescence refrence'
ABSORPTION_NAME  = 'absorption image'
DARK_NAME        = 'dark'
NOATOM_REF_NAME  = 'no atom refrence'

# --- Plot toggle flags ---
SHOW_FLUOR_REF   = 0       # show 'florescence refrence' panel
SHOW_ABSORPTION  = True    # show 'absorption image' panel
SHOW_DARK        = 0       # show 'dark' panel
SHOW_NOATOM_REF  = True    # show 'no atom refrence' panel
SHOW_OD          = True    # show the OD map panel
SHOW_SLICES      = True    # show slice lines on OD + slice curves

# --- 2D Gaussian fit flag ---
FIT_2D_GAUSSIAN  = 0
    # fit an axis-aligned (xy) 2D Gaussian within the
                           # ROI.  If on, 1sigma & 2sigma contours and a peak
                           # marker are drawn on the OD map, and the x/y slice
                           # curves are overlaid with the fitted profile.

# Map image names to their show flags
SHOW_BY_NAME = {
    FLUOR_REF_NAME:  SHOW_FLUOR_REF,
    ABSORPTION_NAME: SHOW_ABSORPTION,
    DARK_NAME:       SHOW_DARK,
    NOATOM_REF_NAME: SHOW_NOATOM_REF,
}


# ============================================================
# 2D Gaussian model (axis-aligned) + helper
# ============================================================
def gaussian_2d(coords, offset, amp, x0, y0, sigma_x, sigma_y):
    """Axis-aligned 2D Gaussian.  coords = (X, Y) meshgrid arrays (or
    flattened).  x -> column, y -> row."""
    x, y = coords
    g = offset + amp * np.exp(
        -((x - x0) ** 2 / (2 * sigma_x ** 2) +
          (y - y0) ** 2 / (2 * sigma_y ** 2)))
    return g.ravel()


def fmt(value, error, sig=2):
    """Format as value(error) with error in the last sig figures, e.g. 5.869(4)."""
    if error == 0 or not np.isfinite(error):
        return f"{value:.4g}"
    exp = int(np.floor(np.log10(abs(error))))
    decimals = max(0, sig - 1 - exp)
    err_int = int(round(error / 10 ** (exp - (sig - 1))))
    return f"{value:.{decimals}f}({err_int})"


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

    # Build a lookup by image name
    img_by_name = {name: img for name, img in zip(image_names, images)}

    # ROI sum for each image
    r0, r1, c0, c1 = ROI
    print("\nROI sums:")
    for j, img in enumerate(images):
        roi_sum = img[r0:r1, c0:c1].sum()
        print(f"  {image_names[j]}: {roi_sum:.0f}")

    # ============================================================
    # Compute absorption OD = -ln( (atom - dark) / (ref - dark) )
    # ============================================================
    od = None
    have_abs = all(n in img_by_name for n in
                   (ABSORPTION_NAME, NOATOM_REF_NAME, DARK_NAME))
    if have_abs:
        atom = img_by_name[ABSORPTION_NAME]
        ref  = img_by_name[NOATOM_REF_NAME]
        dark = img_by_name[DARK_NAME]

        atom_md = atom - dark
        ref_md  = ref - dark

        with np.errstate(divide='ignore', invalid='ignore'):
            ratio = atom_md / ref_md
            od = -np.log(ratio)
        od = np.where(np.isfinite(od), od, np.nan)

        od_roi = od[r0:r1, c0:c1]
        od_sum = np.nansum(od_roi)
        od_mean = np.nanmean(od_roi)
        print("\nAbsorption OD (ROI):")
        print(f"  OD sum (integrated): {od_sum:.2f}")
        print(f"  OD mean:             {od_mean:.4f}")
    else:
        missing = [n for n in (ABSORPTION_NAME, NOATOM_REF_NAME, DARK_NAME)
                   if n not in img_by_name]
        print(f"\nCannot compute OD, missing image(s): {missing}")

    # ============================================================
    # Determine which image panels to show
    # ============================================================
    shown_images = []
    shown_names = []
    for name, img in zip(image_names, images):
        if SHOW_BY_NAME.get(name, True):
            shown_images.append(img)
            shown_names.append(name)

    show_od_panel = (od is not None) and SHOW_OD
    show_slices = (od is not None) and SHOW_SLICES

    # ============================================================
    # 2D Gaussian fit (axis-aligned) within the ROI
    # ============================================================
    fit2d_ok = False
    fit2d = None
    if (od is not None) and FIT_2D_GAUSSIAN:
        cols_roi = np.arange(c0, c1)
        rows_roi = np.arange(r0, r1)
        Xr, Yr = np.meshgrid(cols_roi, rows_roi)   # X=column, Y=row
        Zr = od[r0:r1, c0:c1]

        good = np.isfinite(Zr)
        if good.sum() >= 6:
            x_data = Xr[good].astype(float)
            y_data = Yr[good].astype(float)
            z_data = Zr[good].astype(float)

            offset0 = np.nanpercentile(Zr, 10)
            amp0 = np.nanmax(Zr) - offset0
            w = np.clip(z_data - offset0, 0, None)
            if w.sum() > 0:
                x00 = np.sum(x_data * w) / w.sum()
                y00 = np.sum(y_data * w) / w.sum()
            else:
                x00 = 0.5 * (c0 + c1)
                y00 = 0.5 * (r0 + r1)
            sigma_x0 = (c1 - c0) / 6.0
            sigma_y0 = (r1 - r0) / 6.0
            p0 = [offset0, amp0, x00, y00, sigma_x0, sigma_y0]

            try:
                popt2d, pcov2d = curve_fit(
                    gaussian_2d, (x_data, y_data), z_data, p0=p0, maxfev=20000)
                perr2d = np.sqrt(np.diag(pcov2d))
                (offset_f, amp_f, x0_f, y0_f, sx_f, sy_f) = popt2d
                sx_f = abs(sx_f)
                sy_f = abs(sy_f)

                fit2d_ok = True
                fit2d = {
                    'offset': offset_f, 'amp': amp_f,
                    'x0': x0_f, 'y0': y0_f,
                    'sigma_x': sx_f, 'sigma_y': sy_f,
                    'perr': perr2d,
                    'popt': popt2d,
                }

                integrated_od = amp_f * 2 * np.pi * sx_f * sy_f
                print("\n2D Gaussian fit (OD, within ROI, axis-aligned):")
                print(f"  offset       = {fmt(offset_f, perr2d[0])}")
                print(f"  amp (peak OD)= {fmt(amp_f, perr2d[1])}")
                print(f"  x0 (col)     = {fmt(x0_f, perr2d[2])}")
                print(f"  y0 (row)     = {fmt(y0_f, perr2d[3])}")
                print(f"  sigma_x      = {fmt(sx_f, perr2d[4])} px")
                print(f"  sigma_y      = {fmt(sy_f, perr2d[5])} px")
                print(f"  integrated OD (2*pi*A*sx*sy) = {integrated_od:.4g}")

                run = lyse.Run(lyse.path)
                run.save_result('gauss2d_offset', float(offset_f))
                run.save_result('gauss2d_amp', float(amp_f))
                run.save_result('gauss2d_x0', float(x0_f))
                run.save_result('gauss2d_y0', float(y0_f))
                run.save_result('gauss2d_sigma_x', float(sx_f))
                run.save_result('gauss2d_sigma_y', float(sy_f))
                run.save_result('gauss2d_integrated_od', float(integrated_od))
            except RuntimeError:
                print("\n2D Gaussian fit failed to converge.")
        else:
            print("\n2D Gaussian fit skipped: too few finite pixels in ROI.")

    # ============================================================
    # Slice definitions (through fitted peak if available)
    # ============================================================
    if FIT_2D_GAUSSIAN and fit2d_ok:
        slice_row = int(round(fit2d['y0']))
        slice_col = int(round(fit2d['x0']))
    else:
        slice_row = (r0 + r1) // 2 + slice_x_offset
        slice_col = (c0 + c1) // 2 + slice_y_offset
    slice_row = int(np.clip(slice_row, 0, od.shape[0] - 1)) if od is not None else 0
    slice_col = int(np.clip(slice_col, 0, od.shape[1] - 1)) if od is not None else 0

    # ============================================================
    # Plot raw images + OD map (+ slice curves)
    # ============================================================
    n_panels = len(shown_images)
    if show_od_panel:
        n_panels += 1
    n_slice_panels = 2 if show_slices else 0
    n = n_panels + n_slice_panels

    if n == 0:
        print("\nNothing to plot (all panels disabled).")
    else:
        n_img_panels = len(shown_images) + (1 if show_od_panel else 0)
        ncols = max(n_img_panels, n_slice_panels)
        nrows = 2 if show_slices else 1

        plot_r0 = max(0, r0 - pad)
        plot_r1 = min(images[0].shape[0], r1 + pad)
        plot_c0 = max(0, c0 - pad)
        plot_c1 = min(images[0].shape[1], c1 + pad)

        # extent maps pixels to absolute (col, row) indices; note the
        # (left, right, bottom, top) order with top<bottom so row 0 is up.
        img_extent = [plot_c0, plot_c1, plot_r1, plot_r0]

        vmin = min(img.min() for img in images)
        vmax = max(img.max() for img in images)

        # GridSpec: one extra NARROW column reserved for the OD colorbar so
        # the OD image renders at exactly the same width as the raw panels.
        fig = plt.figure(figsize=(4 * ncols + 0.6, 4 * nrows))
        width_ratios = [1.0] * ncols + [0.06]   # last col = colorbar strip
        gs = gridspec.GridSpec(nrows, ncols + 1, figure=fig,
                               width_ratios=width_ratios)

        #make title
        t_drop = globals_dict.get('t_drop', None)
        title = shot_file.replace('.h5', '')
        if t_drop is not None:
            title += f"   t_drop = {t_drop}"
        fig.suptitle(title)

        from matplotlib.patches import Rectangle

        # helper: make an axis at flat panel index (skips the cbar column)
        def panel_ax(idx):
            rr = idx // ncols
            cc = idx % ncols
            return fig.add_subplot(gs[rr, cc])

        used_cells = set()
        panel_idx = 0

        # --- Raw image panels ---
        for img, image_name in zip(shown_images, shown_names):
            ax = panel_ax(panel_idx)
            used_cells.add((panel_idx // ncols, panel_idx % ncols))
            crop = img[plot_r0:plot_r1, plot_c0:plot_c1]
            disp_gain = gain_florescence if image_name == 'florescence refrence' else gain
            ax.imshow(crop * disp_gain, vmin=vmin, vmax=vmax,
                      cmap='inferno', extent=img_extent, origin='upper')

            roi_rect = Rectangle(
                (c0, r0), c1 - c0, r1 - r0,
                linewidth=1, edgecolor='cyan', facecolor='none',
                linestyle='--'
            )
            ax.add_patch(roi_rect)

            roi_sum = img[r0:r1, c0:c1].sum()
            ax.set_title(f"{image_name}\nROI sum: {roi_sum:.0f}")
            ax.set_xlabel('column (px)')
            ax.set_ylabel('row (px)')
            ax.tick_params()

            if show_slices:
                ax.axhline(slice_row, color=X_COLOR, linewidth=0.8,
                           linestyle='--')
                ax.axvline(slice_col, color=Y_COLOR, linewidth=0.8,
                           linestyle='--')

            panel_idx += 1

        # --- OD map panel ---
        if show_od_panel:
            od_row = panel_idx // ncols
            od_col = panel_idx % ncols
            ax = fig.add_subplot(gs[od_row, od_col])
            used_cells.add((od_row, od_col))
            od_crop = od[plot_r0:plot_r1, plot_c0:plot_c1]
            od_finite = od_crop[np.isfinite(od_crop)]
            if od_finite.size:
                od_vmin = np.nanpercentile(od_finite, 1)
                od_vmax = np.nanpercentile(od_finite, 99)
            else:
                od_vmin, od_vmax = 0, 1
            im = ax.imshow(od_crop, vmin=od_vmin, vmax=od_vmax,
                           cmap='inferno', extent=img_extent, origin='upper')

            roi_rect = Rectangle(
                (c0, r0), c1 - c0, r1 - r0,
                linewidth=1, edgecolor='white', facecolor='none',
                linestyle='--'
            )
            ax.add_patch(roi_rect)

            if show_slices:
                ax.axhline(slice_row, color=X_COLOR, linewidth=0.8,
                           linestyle='--')
                ax.axvline(slice_col, color=Y_COLOR, linewidth=0.8,
                           linestyle='--')

            if FIT_2D_GAUSSIAN and fit2d_ok:
                x0_f = fit2d['x0']; y0_f = fit2d['y0']
                sx_f = fit2d['sigma_x']; sy_f = fit2d['sigma_y']
                ax.plot(x0_f, y0_f, 'x', color='cyan', markersize=10,
                        markeredgewidth=2)
                phi = np.linspace(0, 2 * np.pi, 200)
                for nsig, ls in ((1, '-'), (2, ':')):
                    xe = x0_f + nsig * sx_f * np.cos(phi)
                    ye = y0_f + nsig * sy_f * np.sin(phi)
                    ax.plot(xe, ye, ls, color='cyan', linewidth=1.0)

            ax.set_title(f"OD = -ln((atom-dark)/(ref-dark))\n"
                         f"OD sum: {od_sum:.2f}")
            ax.set_xlabel('column (px)')
            ax.set_ylabel('row (px)')
            ax.tick_params()

            # Colorbar lives in the reserved narrow GridSpec column, in the
            # SAME row as the OD panel -> OD image keeps full panel width.
            cax = fig.add_subplot(gs[od_row, ncols])
            fig.colorbar(im, cax=cax)

            panel_idx += 1

        # --- Slice curve panels ---
        if show_slices:
            # x-slice: OD along columns at slice_row (X_COLOR)
            x_cols = np.arange(c0, c1)
            x_slice = od[slice_row, c0:c1]


            gs_bottom = gs[1, 0:ncols].subgridspec(1, 2)
            ax = fig.add_subplot(gs_bottom[0, 0])
            ax.plot(x_cols, x_slice, '.', color=X_COLOR, markersize=3,
                    label='data')
            if FIT_2D_GAUSSIAN and fit2d_ok:
                xx = x_cols.astype(float)
                yy = np.full_like(xx, float(slice_row))
                x_fit = gaussian_2d((xx, yy), *fit2d['popt'])
                ax.plot(x_cols, x_fit, '-', color=X_COLOR, linewidth=1.4,
                        label='fit')
                x_txt = (
                    r'$f = A + B\,e^{-(x-x_0)^2/2\sigma_x^2}$' + '\n'
                    f"$A$ = {fit2d['offset']:.3g}\n"
                    f"$B$ = {fit2d['amp']:.3g}\n"
                    f"$x_0$ = {fit2d['x0']:.1f} px\n"
                    f"$\\sigma_x$ = {fit2d['sigma_x']:.2f} px"
                )
                ax.text(0.03, 0.97, x_txt, transform=ax.transAxes,
                       va='top', ha='left',
                        bbox=dict(boxstyle='round', facecolor='white',
                                  edgecolor=X_COLOR, alpha=0.85))
            ax.set_xlabel('column (px)')
            ax.set_ylabel('OD')
            ax.set_title(f"x-slice (row {slice_row})",
                         color=X_COLOR)
            ax.grid(True, alpha=0.3)
            ax.tick_params()
            panel_idx += 1

            # y-slice: OD along rows at slice_col (Y_COLOR)
            y_rows = np.arange(r0, r1)
            y_slice = od[r0:r1, slice_col]

            ax = fig.add_subplot(gs_bottom[0, 1])
            ax.plot(y_rows, y_slice, '.', color=Y_COLOR, markersize=3,
                    label='data')
            if FIT_2D_GAUSSIAN and fit2d_ok:
                yy = y_rows.astype(float)
                xx = np.full_like(yy, float(slice_col))
                y_fit = gaussian_2d((xx, yy), *fit2d['popt'])
                ax.plot(y_rows, y_fit, '-', color=Y_COLOR, linewidth=1.4,
                        label='fit')
                y_txt = (
                    r'$f = A + B\,e^{-(y-y_0)^2/2\sigma_y^2}$' + '\n'
                    f"$A$ = {fit2d['offset']:.3g}\n"
                    f"$B$ = {fit2d['amp']:.3g}\n"
                    f"$y_0$ = {fit2d['y0']:.1f} px\n"
                    f"$\\sigma_y$ = {fit2d['sigma_y']:.2f} px"
                )
                ax.text(0.03, 0.97, y_txt, transform=ax.transAxes,
                        fontsize=8, va='top', ha='left',
                        bbox=dict(boxstyle='round', facecolor='white',
                                  edgecolor=Y_COLOR, alpha=0.85))
            ax.set_xlabel('row (px)')
            ax.set_ylabel('OD')
            ax.set_title(f"y-slice (col {slice_col})",
                         color=Y_COLOR)
            ax.grid(True, alpha=0.3)
            ax.tick_params()
            panel_idx += 1

        fig.tight_layout()

    # Save results to lyse so they appear in the dataframe
    run = lyse.Run(lyse.path)
    if od is not None:
        run.save_result('od_sum', float(od_sum))
        run.save_result('od_mean', float(od_mean))
    for name, img in img_by_name.items():
        roi_sum = img[r0:r1, c0:c1].sum()
        key = name.replace(' ', '_') + '_roi_sum'
        run.save_result(key, float(roi_sum))