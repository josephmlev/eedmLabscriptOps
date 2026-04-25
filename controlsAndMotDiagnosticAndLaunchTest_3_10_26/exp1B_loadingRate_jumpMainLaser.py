# Experiment 1B: Loading Rate & Atom Number (Main Laser Jump Shutter)
# 
# Purpose: Same as Exp 1 — measure the MOT loading time constant and 
# steady-state atom number — but using the D2-125 Relative Jump as a 
# fast shutter instead of the mechanical MRR shutter. The main laser 
# is jumped off resonance by asserting MAIN_REL_JUMP_do HIGH with a 
# set voltage on MAIN_JUMP_AMP_ao. When the TTL goes LOW, the servo 
# relocks to the original frequency (<400 µs) and the MOT begins loading.
#
# The repump and mechanical shutters remain open throughout. Only the 
# main cooling laser is toggled via frequency jump.
#
# Sequence: 
#   1. Jump main laser off resonance (effective shutter closed), wait 
#      for MOT to fully disperse
#   2. Take background image (laser off resonance, no MOT)
#   3. Release jump (servo relocks, laser back on resonance)
#   4. Take images at regular intervals as MOT loads
#   5. Take final steady-state reference image
#
# Globals:
#   n_images:       number of images to take during loading (default 20)
#   image_interval: time between images in seconds (default 0.25)
#   disperse_time:  time to wait for MOT to fully disperse (default 3.0)
#   main_jump_V:    voltage on Laser Jump Amplitude for main laser (V).
#                   Sets how far off resonance the laser jumps.
#                   Calibration: ~1 mV/MHz (TBD — see lab notebook).

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
    MRR_SHUTTER_do.open(t)       # MRR shutter stays open throughout
    do6363_0.go_high(t)           # trigger line low
    MAIN_REL_JUMP_do.go_high(t)  # start with main laser jumped off resonance
    REPUMP_REL_JUMP_do.go_low(t) # repump stays on resonance
    MAIN_JUMP_AMP_ao.constant(t, value=main_jump_V)  # set jump amplitude
    REPUMP_JUMP_AMP_ao.constant(t, value=0)

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
    # Wait for MOT to fully disperse with main laser off resonance
    # Light is physically present but far from the atomic transition,
    # so atoms see no scattering force. Equivalent to shutter closed.
    # ============================================================
    add_time_marker(t, "Waiting for MOT to disperse", verbose=True)
    t += disperse_time

    # ============================================================
    # Background image with no atoms
    # Main laser is off resonance, so no MOT fluorescence. Note 
    # that scattered laser light is still present — this background
    # may differ from a true dark-frame background.
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
    # Release jump — servo relocks main laser to resonance (<400 µs)
    # MOT begins loading
    # ============================================================
    add_time_marker(t, "Open shutter, begin loading", verbose=True)
    MAIN_REL_JUMP_do.go_low(t)
    t+=0.001 # small delay to ensure relock before first image
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
    MAIN_REL_JUMP_do.go_low(t)

    t += 0.01
    stop(t)