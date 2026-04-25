# Experiment: PGC + Moving Molasses Launch
#
# Purpose: Sub-Doppler cool the MOT cloud, close the shutter,
# accelerate the MRR stage while shutter is closed, reopen shutter
# so atoms see moving molasses, then red shift ~50us after shutter
# opens for PGC in the moving frame.
#
# Globals:
#   t_load:             MOT loading time in seconds (default 4.0)
#   t_dark:             shutter-closed dark time in seconds (default 0.028)
#   t_hold:             time between molasses images in seconds (default 0.02)
#   v_laser_jump_rel:   red shift amplitude in volts (default -0.05)
#   v_stage:            stage velocity in mm/s (default 5)
#   a_stage:            stage acceleration in mm/s^2 (default 10000)
#   xf_stage:           stage move distance in mm (default 1)

import numpy as np
from labscript import *
from labscriptlib.eedmLabscriptOps.connection_table import ct

if __name__ == "__main__":
    ct()
    start()

    t = 0

    # --- Runmanager globals with defaults ---
    try:
        t_load
    except NameError:
        t_load = 4.0

    try:
        t_dark
    except NameError:
        t_dark = 0.028

    try:
        t_hold
    except NameError:
        t_hold = 0.02

    try:
        v_laser_jump_rel
    except NameError:
        v_laser_jump_rel = -0.05

    try:
        v_stage
    except NameError:
        v_stage = 5

    try:
        a_stage
    except NameError:
        a_stage = 10000

    try:
        xf_stage
    except NameError:
        xf_stage = 1

    # --- Stage kinematics ---
    MRR_stage_delay = 6e-3
    MRR_shutter_min_time = 0.012
    MOT_coil_delay = 0.003

    t_accel = v_stage / a_stage
    d_accel = 0.5 * a_stage * t_accel**2
    xi_stage = np.round((150 - d_accel - 0.25), 1)

    if d_accel > abs(xf_stage - xi_stage):
        raise ValueError("Target velocity too high for move distance and acceleration.")

    # --- Configure stage ---
    bbd301.set_velocity(1, v_stage)
    bbd301.set_acceleration(1, a_stage)
    bbd301.set_move_distance(1, xf_stage)
    bbd301.set_reset_position(1, 149)

    # ============================================================
    # Initialize outputs -- normal MOT state
    # ============================================================
    MOT_COIL_do.go_high(t)
    MRR_SHUTTER_do.open(t)
    MOT_SHUTTER_do.close(t)
    REPUMP_SHUTTER_do.open(t)
    MAIN_REL_JUMP_do.go_low(t)
    REPUMP_REL_JUMP_do.go_low(t)
    LCR_do.go_high(t)
    MRR_TRIG_do.go_low(t)
    MAIN_JUMP_AMP_ao.constant(t, v_laser_jump_rel)

    t += 0.01

    # ============================================================
    # Load MOT
    # ============================================================
    add_time_marker(t, "Loading MOT", verbose=True)
    t += t_load

    # ============================================================
    # Reference image
    # ============================================================
    add_time_marker(t, "Reference image", verbose=True)
    my_ids_camera.expose(
        t=t, name='reference', frametype='atom',
        trigger_duration=1*ms
    )
    t += 0.01

    # ============================================================
    # MOT coils off for molasses
    # ============================================================
    add_time_marker(t, "MOT coils off", verbose=True)
    MOT_COIL_do.go_low(t)
    t += MOT_coil_delay

    # ============================================================
    # Sub-Doppler cooling (PGC) -- red shift on
    # ============================================================
    add_time_marker(t, "PGC red shift on", verbose=True)
    MAIN_REL_JUMP_do.go_high(t)
    t += 0.005

    # ============================================================
    # Close shutter -- dark time begins
    # ============================================================
    add_time_marker(t, "Shutter close -- dark time", verbose=True)
    MRR_SHUTTER_do.close(t)
    MAIN_REL_JUMP_do.go_low(t+0.003)

    # ============================================================
    # Trigger stage to accelerate while shutter is closed
    # ============================================================
    add_time_marker(t, "Trigger MRR stage", verbose=True)
    MRR_TRIG_do.go_high(t + 0.001)
    MRR_TRIG_do.go_low(t + 0.011)

    # Wait for dark time or stage to reach speed, whichever is longer
    t_stage_ready = t_accel + MRR_stage_delay
    t += max(t_dark, t_stage_ready)

    # ============================================================
    # Reopen shutter -- atoms now see moving molasses
    # ============================================================
    add_time_marker(t, "Shutter open -- moving molasses", verbose=True)
    MRR_SHUTTER_do.open(t)

    wait("shutter open", t, timeout=0.1)
    t += 0.002  # wait for shutter to fully open
    REPUMP_REL_JUMP_do.go_high(t)  # repump jump is used as a trigger for scope
    #my_ids_camera.expose(
    #    t=t, name='moving molasses', frametype='atom',
    #    trigger_duration=1*ms
    #)

    # ============================================================
    # Red shift on ~50 us after shutter open -- PGC in moving frame
    # ============================================================
    add_time_marker(t, "Red shift on -- PGC in moving frame", verbose=True)
    #t += 0.001
    MAIN_REL_JUMP_do.go_high(t)

    # ============================================================
    # First molasses image -- moving molasses
    # ============================================================
    add_time_marker(t, "Molasses image 1 -- moving", verbose=True)

    t += t_hold

    MAIN_REL_JUMP_do.go_low(t)
    t+=0.001
    # ============================================================
    # Second molasses image
    # ============================================================
    add_time_marker(t, "Molasses image 2 -- late", verbose=True)
    my_ids_camera.expose(
        t=t, name='molasses_late', frametype='atom',
        trigger_duration=1*ms
    )

    # ============================================================
    # Cleanup -- return to normal MOT state
    # ============================================================
    t += 0.01
    MAIN_REL_JUMP_do.go_low(t)
    MOT_COIL_do.go_high(t)
    MRR_SHUTTER_do.open(t)
    REPUMP_SHUTTER_do.open(t)
    REPUMP_REL_JUMP_do.go_low(t)

    t += 2
    stop(t)