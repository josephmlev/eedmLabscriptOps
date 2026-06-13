# Experiment: MOT + MRR Launch with PGC
#
# Purpose: Form MOT on MOT arm, accelerate MRR stage, PGC cool,
# switch to MRR arm, open shutter, PGC in moving frame, image.
#
# Globals:
#   t_load:             MOT loading time in seconds (default 4.0)
#   t_dark:             shutter-closed dark time in seconds (default 0.028)
#   t_hold:             time between molasses images in seconds (default 0.02)
#   t_redshift:         PGC duration before closing shutter in seconds (default 0.005)
#   t_redshift_launch:     PGC duration in moving frame in seconds (default 0.005)
#   v_laser_jump_rel:   red shift amplitude in volts (default -0.05)
#   v_stage:            stage velocity in mm/s (default 5)
#   a_stage:            stage acceleration in mm/s^2 (default 10000)
#   xf_stage:           stage move distance in mm (default 1)

import numpy as np
from labscript import *
from labscriptlib.eedmLabscriptOps.connection_table import ct
from labscript import compiler


def set_beam_path(t, mode):
    """Switch beam path between 'MOT' and 'MRR'."""
    if mode == 'MOT': #set LCR to V2 (low) #note, old liquid crystal controller is BACKWARDS from new one, high = MOT 
        #MOT_SHUTTER_do.open(t)
        #MRR_SHUTTER_do.close(t)
        LCR_do.go_high(t)
        LCR_BOT_do.go_low(t)
        #LCR_HOR_ao.constant(t, 0.0)
        LCR_TOP_ao.constant(t, 0.0)
    elif mode == 'MRR': #set LCR to V1 (high)
        #MOT_SHUTTER_do.close(t)
        #MRR_SHUTTER_do.open(t)
        LCR_do.go_low(t)
        #LCR_BOT_do.go_high(t)
        #LCR_HOR_ao.constant(t, 5.0)
        #LCR_TOP_ao.constant(t, 5.0)
    else:
        raise ValueError(f"Unknown beam path mode: {mode}. Use 'MOT' or 'MRR'.")


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
        t_redshift
    except NameError:
        t_redshift = 0.005

    try:
        t_redshift_launch
    except NameError:
        t_redshift_launch = 0.005

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
    bbd301.set_reset_position(1, 150)

 

    # ============================================================
    # Initialize outputs -- MOT arm, everything normal
    # ============================================================
    MOT_COIL_do.go_low(t)
    REPUMP_SHUTTER_do.open(t)
    MAIN_REL_JUMP_do.go_low(t)
    #REPUMP_REL_JUMP_do.go_low(t)
    MRR_TRIG_do.go_low(t)
    #MAIN_JUMP_AMP_ao.constant(t, v_laser_jump_rel)
    MAIN_JUMP_AMP_ao.constant(t, 0.0)
    set_beam_path(t, 'MOT')
    MOT_SHUTTER_do.close(t)
    MRR_SHUTTER_2_do.close(t)
    MRR_SHUTTER_do.open(t)
    

    LCR_HOR_ao.constant(t, 5.0)
    
    #MOT_SHUTTER_do.open(t)
    #MRR_SHUTTER_do.open(t)
    #LCR_do.go_high(t)
    #LCR_HOR_ao.constant(t, 5.0)
    #LCR_BOT_do.go_low(t)
    #LCR_TOP_ao.constant(t, 5.0)

    t += 0.25
    #MOT_SHUTTER_do.open(t)
    MOT_COIL_do.go_high(t)
    MOT_SHUTTER_do.open(t)


    # ============================================================
    # Load MOT on MOT arm
    # ============================================================
    add_time_marker(t, "Loading MOT", verbose=True)
    t += t_load

    # ============================================================
    # Reference image -- MOT in home position
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
    t += 0.01

    # ============================================================
    # PGC on MOT arm -- red shift on
    # ============================================================
    add_time_marker(t, "PGC on MOT arm", verbose=True)
    MAIN_JUMP_AMP_ao.constant(t-0.001, v_laser_jump_rel)
    MAIN_REL_JUMP_do.go_high(t)
    t += t_redshift

    # ============================================================
    # Close MOT shutter -- dark time begins
    # Atoms in the dark, stage still accelerating
    # ============================================================
    add_time_marker(t, "Close MOT shutter -- dark time", verbose=True)
    MOT_SHUTTER_do.close(t)
    
    #scope_trig_do.go_high(t)#using this as a scope trigger. Delete this
    #scope_trig_do.go_low(t+0.1)
    #t_trig = t

    t += 0.002
    #REPUMP_SHUTTER_do.close(t)
    MAIN_REL_JUMP_do.go_low(t)
    MAIN_JUMP_AMP_ao.constant(t+0.001, 0.00)
    

    add_time_marker(t, "Switch to MRR arm", verbose=True)
    set_beam_path(t, 'MRR')
    #LCR_TOP_ao.constant(t, 5.0)

    t += t_dark 
    # ============================================================
    # Switch to MRR arm -- LCRs flip during dark time
    # ============================================================

    MRR_SHUTTER_2_do.open(t)



    # ============================================================
    # Wait for photodiode trigger confirming shutter is open
    # ============================================================
    add_time_marker(t, "Wait for shutter open trigger", verbose=True)
    wait("mrr_shutter_open", t, timeout=0.1)
    

    #ai0.acquire(label='TOF_florescence', start_time = t, end_time =t+0.1)

    
    #============================================================
    #PGC in moving frame -- red shift on ~50 us after shutter open
    #============================================================
    
    MAIN_JUMP_AMP_ao.constant(t, -0.05)

    my_ids_camera.expose(
    t=t+0.0005, name=f'molasses', frametype='atom',
    trigger_duration=1*ms)

    
    #t += 1000e-6 #works for drop
    t += 0.001


    add_time_marker(t, "PGC in 'moving' frame", verbose=True)
    MAIN_REL_JUMP_do.go_high(t)
    #MAIN_JUMP_AMP_ao.ramp(t-0.0005, 0.002, 0, -.15, 1e5)
    #t += 0.01 #works for drop
    t+= 0.01
    MRR_SHUTTER_do.close(t)

    scope_trig_do.go_high(t)
    scope_trig_do.go_low(t+0.02)
    t_trig = t

    drop_time = t  # atoms begin free fall here
    compiler.shot_properties['drop_time'] = drop_time
    ai0.acquire(label='TOF_florescence', start_time = drop_time + 0.12, end_time =drop_time+0.16)


    #============================================================
     #Jump back on resonance for imaging
    #============================================================
    MAIN_REL_JUMP_do.go_low(t+0.001)
    
    #jump probe to blue
    t += 0.001
    MAIN_JUMP_AMP_ao.constant(t, 0.01)
    t += 0.11
    
    MAIN_REL_JUMP_do.go_high(t)
    MAIN_REL_JUMP_do.go_low(t+0.05)
    
    #REPUMP_SHUTTER_do.close(t)
    '''
    t += t_camera_delay
    my_ids_camera.expose(
    t=t, name=f'molasses', frametype='atom',
    trigger_duration=1*ms)'''
    '''
    # ============================================================
    # Molasses images
    # ============================================================
    for i in range(1):
        add_time_marker(t, f"Molasses image {i}", verbose=True)
        my_ids_camera.expose(
            t=t, name=f'molasses_{i}', frametype='atom',
            trigger_duration=1*ms
        )
        t += t_hold
    '''
    # ============================================================
    # Cleanup -- return to MOT arm, normal state
    # ============================================================
    t += .2
    MAIN_REL_JUMP_do.go_low(t)
    #REPUMP_REL_JUMP_do.go_low(t)
    MOT_COIL_do.go_high(t)
    set_beam_path(t, 'MOT')
    REPUMP_SHUTTER_do.open(t)
    MOT_SHUTTER_do.open(t)
    MRR_SHUTTER_2_do.close(t)

    t += .1
    stop(t)