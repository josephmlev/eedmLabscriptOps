# Experiment 1: Loading Rate & Atom Number
# 
# Purpose: Measure the MOT loading time constant and steady-state atom
# number. Close the shutter to let the MOT fully disperse, then open it
# and take images at fixed intervals to watch the fluorescence rise.
# Fit an exponential to the total pixel counts in a region of interest
# to extract the loading time constant and steady-state value.
#
# Sequence: 
#   1. Close shutter, wait for MOT to fully disperse (~3-5 seconds)
#   2. Open shutter with coils on
#   3. Take images at regular intervals as MOT loads
#
# Globals:
#   n_images: number of images to take during loading (default 20)
#   image_interval: time between images in seconds (default 0.25)
#   disperse_time: time to wait for MOT to fully disperse (default 3.0)

import numpy as np
from labscript import *
from labscriptlib.eedmLabscriptOps.connection_table import ct

if __name__ == "__main__":
    ct()
    start()

    # Initialize time and state of outputs
    t = 0
    MOT_COIL_do.go_high(t)       # coils on for the whole shot
    MRR_TRIG_do.go_low(t)        # MRR not used
    MRR_SHUTTER_do.close(t)      # start with shutter closed
    do6363_0.go_low(t)           # trigger line low

    t += 0.01  # 10 ms buffer

    # --- Timing parameters ---
    # Set these as globals in runmanager, or use defaults here
    try:
        n_images
    except NameError:
        n_images = 20

    try:
        image_interval
    except NameError:
        image_interval = 0.25 

    try:
        disperse_time
    except NameError:
        disperse_time = 3.0  # 3 seconds for MOT to fully empty

    # ============================================================
    # Wait for MOT to fully disperse with shutter closed
    # The MOT should already be dispersed if shutter starts closed,
    # but we wait to be sure. Coils stay on — doesn't matter with
    # no light.
    # ============================================================
    add_time_marker(t, "Waiting for MOT to disperse", verbose=True)
    t += disperse_time

    # ============================================================
    # Background image with no atoms
    # Shutter is closed, so no MOT light. This gives a background
    # frame for subtraction — camera noise, ambient light, etc.
    # ============================================================
    add_time_marker(t, "Background image", verbose=True)
    my_ids_camera.expose(
        t=t,
        name='background',
        frametype='atom',
        trigger_duration=1*ms
    )
    t += 0.01  # 10 ms for camera refresh

    # ============================================================
    # Open shutter and start taking images as MOT loads
    # ============================================================
    add_time_marker(t, "Open shutter, begin loading", verbose=True)
    MRR_SHUTTER_do.open(t)
    t+=0.001 # small delay to ensure shutter is open before first image
    # ============================================================
    # Take images at regular intervals during loading
    # ============================================================
    for i in range(n_images):
        add_time_marker(t, f"Loading image {i}", verbose=True)
        my_ids_camera.expose(
            t=t,
            name=f'loading_{i:03d}',
            frametype='atom',
            trigger_duration=1*ms
        )
        t += image_interval

    # ============================================================
    # Take a final steady-state reference image
    # MOT should be fully loaded by now. This is your baseline
    # fluorescence for atom number comparisons in later experiments.
    # ============================================================
    add_time_marker(t, "Steady-state reference", verbose=True)
    t += 1.0  # extra second to make sure we're at steady state
    my_ids_camera.expose(
        t=t,
        name='steady_state',
        frametype='atom',
        trigger_duration=1*ms
    )

    # ============================================================
    # Cleanup: leave everything in a good state for next shot
    # ============================================================
    t += 0.1
    MOT_COIL_do.go_high(t)
    MRR_SHUTTER_do.open(t)

    t += 0.01
    stop(t)