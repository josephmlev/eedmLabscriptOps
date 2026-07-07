# Experiment: Absorption Imaging
#
# Purpose: Absorption imaging of the MOT.
#   1. MOT is up between shots.
#   2. Kill MOT.
#   3. Take a dark photo a few ms before beginning to load.
#   4. Open shutters, coils off, take a light (reference) photo.
#   5. Coils on, load for t_load.
#   6. Close MOT shutter and repump, open probe shutter, take atom image.
#      Then let atoms clear and take reference frame back-to-back.
#
# Globals to define in runmanager:
#   t_load:         MOT loading time in seconds (e.g. 4.0)
#   t_dark:         time-of-flight before atom probe pulse in seconds (e.g. 0.001)
#   t_clear:        time to let atoms clear between atom and reference frames (e.g. 0.02)
#   t_settle:       extra light-stability margin before exposing (e.g. 0.002)
#   exposure_time:  camera exposure, set via config table (not used in script)
#   gain:           camera gain, set via config table (not used in script)

import numpy as np
from labscript import *
from labscriptlib.eedmLabscriptOps.connection_table import ct
from labscript import compiler


if __name__ == "__main__":
    ct()
    start()

    t = 0

    # ============================================================
    # Initialize outputs -- kill mot
    # ============================================================
    MOT_COIL_do.go_low(t)
    REPUMP_SHUTTER_do.close(t)
    MRR_TRIG_do.go_low(t)
    MOT_SHUTTER_do.close(t)
    PROBE_SHUTTER_do.close(t)
    LCR_do.go_high(t)
    LCR_BOT_do.go_low(t)
    LCR_TOP_ao.constant(t, 0.0)


    MAIN_REL_JUMP_do.go_low(t)
    MAIN_JUMP_AMP_ao.constant(t, v_rel_jump)

    t += 0.25  # let MOT clear out 

    #load MOT
    MOT_COIL_do.go_high(t)
    REPUMP_SHUTTER_do.open(t)
    MOT_SHUTTER_do.open(t)
    t+=t_load


    my_ids_camera.expose(
        t=t, name='florescence refrence', frametype='atom',
        trigger_duration=1*ms
    )
    t+= 0.05 #wait for camera


    MOT_COIL_do.go_low(t)
    t+=0.01
    #PGC
    #MAIN_REL_JUMP_do.go_high(t)
    #MAIN_JUMP_AMP_ao.ramp(t-0.0005, 0.0051, -0.0, -.1, 1e5) #(t, duration, initial, final, samplerate)
    
    MAIN_JUMP_AMP_ao.constant(t-0.001, -0.05)
    MAIN_REL_JUMP_do.go_high(t)
    t+= 0.007
    
    
    MOT_SHUTTER_do.close(t)
    #REPUMP_SHUTTER_do.close(t)
    MAIN_REL_JUMP_do.go_low(t)
    t+= t_drop
    PROBE_SHUTTER_do.open(t)
    if relJump:
        MAIN_REL_JUMP_do.go_high(t)
        MAIN_JUMP_AMP_ao.constant(t, v_rel_jump)

    t+= t_settle
    my_ids_camera.expose(
        t=t, name='absorption image', frametype='atom',
        trigger_duration=1*ms
    )

    t+=0.001
    MAIN_REL_JUMP_do.go_low(t)


    t+= 0.1


    #MOT_SHUTTER_do.open(t)
    #REPUMP_SHUTTER_do.open(t)
    if relJump:
        MAIN_REL_JUMP_do.go_high(t)
    #PROBE_SHUTTER_do.open(t)

    t+= t_settle

    my_ids_camera.expose(
        t=t, name='no atom refrence', frametype='atom',
        trigger_duration=1*ms
    )

    t += 0.005

    PROBE_SHUTTER_do.close(t)
    MOT_COIL_do.go_low(t-0.01)
    MOT_SHUTTER_do.close(t)
    REPUMP_SHUTTER_do.close(t)
    t+= 0.25
    
    my_ids_camera.expose(
        t=t, name='dark', frametype='atom',
        trigger_duration=1*ms
    )

   
    # ============================================================
    # Cleanup -- return to MOT-up state between shots
    # ============================================================
    add_time_marker(t, "Cleanup -- MOT back up", verbose=True)
    PROBE_SHUTTER_do.close(t)
    REPUMP_SHUTTER_do.open(t)
    MAIN_REL_JUMP_do.go_low(t)
    MAIN_JUMP_AMP_ao.constant(t, 0.0)
    MOT_COIL_do.go_high(t)
    MOT_SHUTTER_do.open(t)

    t += 0.1
    stop(t)