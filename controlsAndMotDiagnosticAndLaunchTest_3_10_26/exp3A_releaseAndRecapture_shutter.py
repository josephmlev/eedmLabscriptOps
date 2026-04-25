# Experiment 3A: Release and Recapture Temperature (Mechanical Shutter)
# 
# Purpose: Estimate cloud temperature via the fraction of atoms 
# recaptured after a variable dark time with all light off.
#
# Multi-shot experiment: each shot gives one data point 
# (t_dark, recaptured_fraction). Scan t_dark in runmanager.
#
# Both the MRR shutter and repump shutter close simultaneously to 
# ensure truly ballistic expansion with no light forces. Coils stay 
# on so the MOT trapping forces are immediately present when shutters 
# reopen. Image as soon as shutters open to minimize contamination 
# from fresh vapor loading (~1s timescale).
#
# Globals:
#   t_dark:   dark time in seconds (scan in runmanager, e.g. 
#             [0.012, 0.015, 0.020, 0.025, 0.030, 0.040, 0.050, 
#              0.065, 0.080, 0.100])
#   t_load:   MOT loading time in seconds (default 4.0)

import numpy as np
from labscript import *
from labscriptlib.eedmLabscriptOps.connection_table import ct

if __name__ == "__main__":
    ct()
    start()

    t = 0

    # Initialize outputs — MOT on, everything else quiet
    MOT_COIL_do.go_high(t)        # coils on for the whole shot (including dark time)
    MRR_SHUTTER_do.open(t)        # main beam shutter open
    MOT_SHUTTER_do.close(t)        # MOT shutter not used
    REPUMP_SHUTTER_do.open(t)     # repump shutter open
    MAIN_REL_JUMP_do.go_low(t)    # lasers on resonance
    REPUMP_REL_JUMP_do.go_low(t)
    LCR_do.go_high(t)             # LCR on for MRR beam
    MAIN_JUMP_AMP_ao.constant(t, 0.2)  
    REPUMP_JUMP_AMP_ao.constant(t, 3)  

    t += 0.01  # 10 ms buffer

    # --- Runmanager globals with defaults ---
    try:
        t_dark
    except NameError:
        t_dark = 0.030  # 30 ms default

    try:
        t_load
    except NameError:
        t_load = 4.0  # 4 seconds, ~4 time constants

    # ============================================================
    # Load MOT to steady state
    # ============================================================
    add_time_marker(t, "Loading MOT", verbose=True)
    t += t_load

    # ============================================================
    # Steady-state reference image
    # This is the denominator for recaptured fraction.
    # ============================================================
    add_time_marker(t, "Reference image", verbose=True)
    my_ids_camera.expose(
        t=t, name='reference', frametype='atom',
        trigger_duration=1*ms
    )
    t += 0.01  # camera recovery

    # ============================================================
    # Close both shutters — dark time begins
    # Atoms expand ballistically and fall under gravity.
    # Coils stay on so B-field gradient is present at recapture.
    # Scope trigger marks the start of dark time for timing checks.
    # ============================================================
    add_time_marker(t, "Shutters close dark time", verbose=True)
    MRR_SHUTTER_do.close(t)
    #REPUMP_SHUTTER_do.close(t)
    #MAIN_REL_JUMP_do.go_high(t)    # jump main beam off resonance
    #REPUMP_REL_JUMP_do.go_high(t)  # jump repump off resonance
    #MOT_COIL_do.go_low(t)

    t += t_dark 
    # ============================================================
    # Reopen both shutters — recapture
    # Image immediately: MOT reloading from vapor has ~1s time 
    # constant, so the first ~10ms of fluorescence after reopen 
    # is almost entirely recaptured atoms.
    # ============================================================
    add_time_marker(t, "Shutters open recapture", verbose=True)
    MRR_SHUTTER_do.open(t)
    #REPUMP_SHUTTER_do.open(t)
    #MAIN_REL_JUMP_do.go_low(t)    # jump main beam back on resonance
    #REPUMP_REL_JUMP_do.go_low(t)  # jump repump back on resonance
    #MOT_COIL_do.go_high(t)
    t += .001  # small buffer before imaging
    my_ids_camera.expose(
        t=t, name='recapture', frametype='atom',
        trigger_duration=1*ms
    )

    # ============================================================
    # Cleanup: leave everything in a good state
    # ============================================================
    t += 0.1
    MOT_COIL_do.go_high(t)
    MRR_SHUTTER_do.open(t)
    REPUMP_SHUTTER_do.open(t)

    t += 0.01
    stop(t)