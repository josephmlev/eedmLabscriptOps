# view_image.py — single-shot routine for lyse
import lyse
from lyse import Run, path
import matplotlib.pyplot as plt
import numpy as np

run = Run(path)
ser = lyse.data(path)
drop_time = ser['drop_time']

# Helper to handle multi-frame images
def get_single_image(run, device, name, frametype):
    img = run.get_image(device, name, frametype)
    if img.ndim == 3:
        img = img[0]
    return img

# Collect all images with their labels
images = []
labels = []

# Reference image
try:
    images.append(get_single_image(run, 'my_ids_camera', 'reference_image', 'atom'))
    labels.append('Reference')
except Exception:
    pass

# Delayed image (after shutter reopen)
try:
    images.append(get_single_image(run, 'my_ids_camera', 'delayed image', 'atom'))
    labels.append(f'Delayed\ndrop={drop_time*1e3:.1f} ms')
except Exception:
    pass

# Molasses images
for i in range(5):
    try:
        images.append(get_single_image(run, 'my_ids_camera', f'molasses_image {i}', 'atom'))
        labels.append(f'Molasses {i}')
    except Exception:
        break

# Plot
n = len(images)
if n > 0:
    fig, axes = plt.subplots(1, n, figsize=(4 * n, 4))
    if n == 1:
        axes = [axes]
    for ax, img, label in zip(axes, images, labels):
        ax.imshow(img, cmap='gray')
        ax.set_title(label)
    plt.tight_layout()

# Save scalar results for multi-shot analysis
if len(images) > 0:
    run.save_result('ref_total_counts', float(np.sum(images[0])))
if len(images) > 1:
    run.save_result('delayed_total_counts', float(np.sum(images[1])))