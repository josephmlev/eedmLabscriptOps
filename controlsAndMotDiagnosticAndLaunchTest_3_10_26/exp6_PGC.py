# Experiment: PGC Optical Molasses. Sequency from Feiberg notes (May 6 2024)
#
# Purpose: Sub-Doppler cool the MOT cloud, close the shutter to let
# atoms fall in the dark, reopen and image the dropped cloud.
# Nulling coils on, MOT coils turn off before red shift.
#
# Single-shot experiment: takes three images per shot:
#   1. Reference MOT image (steady state)
#   2. Molasses image after dark time (cloud dropped)
#   3. Late molasses image (cloud held by molasses)
#
# Globals:
#   t_load:         MOT loading time in seconds (default 4.0)
#   t_redshift:      time to hold red shift on before closing shutter in seconds (default 0.002)
#   t_dark:         shutter-closed dark time in seconds (default 0.028)
#   t_hold:         time to hold molasses after reopening shutter in seconds (default 0.02)
#   v_laser_jump_rel:    red shift amplitude in volts (default  -0.05)

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
        t_redshift
    except NameError:
        t_redshift = 0.002  # 2 ms


    try:
        t_dark
    except NameError:
        t_dark = 0.028  # 28 ms

    try:
        t_hold
    except NameError:
        t_hold = 0.02 

    try:
         v_laser_jump_rel
    except NameError:
         v_laser_jump_rel = -0.05

    # ============================================================
    # Initialize outputs -- MOT on, everything running normally
    # ============================================================
    MOT_COIL_do.go_high(t)
    MRR_SHUTTER_do.open(t)
    MOT_SHUTTER_do.close(t)
    REPUMP_SHUTTER_do.open(t)
    MAIN_REL_JUMP_do.go_low(t)    # on resonance
    REPUMP_REL_JUMP_do.go_low(t)  # on resonance
    LCR_do.go_high(t)               #using MRR beam
    MAIN_JUMP_AMP_ao.constant(t, v_laser_jump_rel)

    t += 0.01  # 10 ms buffer

    # ============================================================
    # Load MOT to steady state
    # ============================================================
    add_time_marker(t, "Loading MOT", verbose=True)
    t += t_load

    # ============================================================
    # Reference image -- MOT in home position, everything normal
    # ============================================================
    add_time_marker(t, "Reference image", verbose=True)
    my_ids_camera.expose(
        t=t, name='reference', frametype='atom',
        trigger_duration=1*ms
    )
    t += 0.01  # camera recovery

    # ============================================================
    # Turn off MOT coils
    # Coils off so B-field gradient goes to zero for molasses.
    # ============================================================
    add_time_marker(t, "MOT coils off", verbose=True)
    MOT_COIL_do.go_low(t)

    t += 0.003  # 3 ms for coil field to decay

    # ============================================================
    # Red shift laser for sub-Doppler cooling
    # Jump both main and repump off resonance to the red.
    # Atoms cool below Doppler limit during this phase.
    # ============================================================
    add_time_marker(t, "Red shift on", verbose=True)
    MAIN_REL_JUMP_do.go_high(t)

    #REPUMP_REL_JUMP_do.go_high(t)

    t += t_redshift  # hold red shift for specified time before closing shutter  

    # ============================================================
    # Close shutter -- dark time begins
    # Atoms fall under gravity with no light forces.
    # ============================================================
    add_time_marker(t, "Shutter close -- dark time", verbose=True)
    MRR_SHUTTER_do.close(t)
    #REPUMP_SHUTTER_do.close(t)

    t += t_dark

    # ============================================================
    # Reopen shutters -- molasses resumes
    # Cloud should have dropped during dark time.
    # ============================================================
    add_time_marker(t, "Shutters open -- molasses resumes", verbose=True)
    MRR_SHUTTER_do.open(t)
    #REPUMP_SHUTTER_do.open(t)
    MAIN_REL_JUMP_do.go_low(t)    # back on resonance
    #REPUMP_REL_JUMP_do.go_low(t)

    # ============================================================
    # First molasses image -- cloud has dropped
    # ============================================================
    add_time_marker(t, "Molasses image 1 -- dropped cloud", verbose=True)
    my_ids_camera.expose(
        t=t, name='molasses_early', frametype='atom',
        trigger_duration=1*ms
    )

    t += t_hold  # wait for hold time

    # ============================================================
    # Second molasses image -- cloud held by molasses force
    # ============================================================
    add_time_marker(t, "Molasses image 2 -- held cloud", verbose=True)
    my_ids_camera.expose(
        t=t, name='molasses_late', frametype='atom',
        trigger_duration=1*ms
    )

    # ============================================================
    # Cleanup -- return to normal MOT state
    # ============================================================
    t += 0.1
    MOT_COIL_do.go_high(t)
    MRR_SHUTTER_do.open(t)
    REPUMP_SHUTTER_do.open(t)
    MAIN_REL_JUMP_do.go_low(t)
    REPUMP_REL_JUMP_do.go_low(t)

    t += 0.01
    stop(t)