# Experiment 2: MOT Lifetime (Magnetic Field Kill)
#
# Purpose: Measure the MOT lifetime by loading to steady state, then
# killing the magnetic field and watching the atoms disperse. Take a
# single image at a variable delay after the field is killed. Repeat
# across shots with different delays to map out the decay curve.
#
# Sequence:
#   1. Close shutter, coils off, wait for MOT to fully disperse
#   2. Take a background image (no atoms, no light)
#   3. Open shutter, coils on, load MOT to steady state
#   4. Take a steady-state reference image
#   5. Kill magnetic field (coils off), shutter stays open
#   6. Wait a variable delay (kill_delay)
#   7. Take a single image to measure remaining atoms
#   8. Restore coils and shutter for next shot
#
# Globals:
#   load_time: time to let MOT load to steady state (default 3.0 s)
#   image_delay: time after coils off before taking image (seconds, scanned in runmanager)
#   disperse_time: time to wait with shutter closed at start (default 3.0 s)

import numpy as np
from labscript import *
from labscriptlib.eedmLabscriptOps.connection_table import ct

if __name__ == "__main__":
    ct()
    start()

    # Initialize time and state of outputs
    t = 0
    MOT_COIL_do.go_high(t)       # coils on
    MRR_SHUTTER_do.close(t)      # start with shutter closed
    do6363_0.go_low(t)           # trigger line low

    t += 0.01  # 10 ms buffer

    # --- Timing parameters ---
    try:
        load_time
    except NameError:
        load_time = 3.0

    try:
        image_delay
    except NameError:
        image_delay = 0.01  # default 10 ms

    try:
        disperse_time
    except NameError:
        disperse_time = 3.0


    # ============================================================
    # Background image — no atoms, no light
    # ============================================================
    add_time_marker(t, "Background image", verbose=True)
    my_ids_camera.expose(
        t=t,
        name='background',
        frametype='atom',
        trigger_duration=1*ms
    )
    t += 0.01

    # ============================================================
    # Open shutter, load MOT to steady state
    # ============================================================
    add_time_marker(t, "Open shutter, loading MOT", verbose=True)
    MRR_SHUTTER_do.open(t)
    t += load_time

    # ============================================================
    # Steady-state reference image (fully loaded MOT)
    # ============================================================
    add_time_marker(t, "Steady-state reference image", verbose=True)
    my_ids_camera.expose(
        t=t,
        name='steady_state',
        frametype='atom',
        trigger_duration=1*ms
    )
    t += 0.01

    # ============================================================
    # Kill magnetic field — atoms begin to disperse
    # ============================================================
    add_time_marker(t, "Kill coils", verbose=True)
    MOT_COIL_do.go_low(t)

    # ============================================================
    # Wait the variable delay, then take image
    # ============================================================
    t += image_delay
    add_time_marker(t, f"Decay image at delay={image_delay*1000:.1f} ms", verbose=True)
    my_ids_camera.expose(
        t=t,
        name='decay',
        frametype='atom',
        trigger_duration=1*ms
    )

    # ============================================================
    # Cleanup: restore coils and shutter for next shot
    # ============================================================
    t += 0.1
    MOT_COIL_do.go_high(t)
    MRR_SHUTTER_do.open(t)

    t += 0.01
    stop(t)