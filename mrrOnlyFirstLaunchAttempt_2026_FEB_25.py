# MRR launch sequence, first pass. Follows Harvey's notes from the
# 2/23/26 to-do list. This only runs the MRR beam path — no MOT beam
# switching. Takes a reference image, closes the shutter, triggers the
# stage to accelerate to 15 mm/s while the shutter closes, kills the
# MOT coils once the shutter is fully closed, then reopens the shutter
# and takes a molasses image. Tries to minimize free-fall time by
# overlapping the stage acceleration with the shutter close. Timing
# and shutter polarity probably need tuning.

import numpy as np
from labscript import *
from labscriptlib.eedmLabscriptOps.connection_table import ct

if __name__ == "__main__":
    ct()
    start()

    #Initialize time and state of outputs
    t= 0 
    MOT_COIL_do.go_high(t)  # turn on MOT coils. Should already be on from last time!
    MRR_TRIG_do.go_low(t) 
    MRR_SHUTTER_do.open(t)
    do6363_0.go_high(t)  # trigger for testing, remove later
    t += 0.01 # start 10 ms after t=0 to give shutter delay time to be included.


    #init varables for timing
    dt = 1e-2  # 10 ms base time step
    MRR_stage_delay = 6e-3    # max time for stage to respond to trig. 2026 FEB 27 in lab book 
    MRR_shutter_min_time = 0.011 #min time shutter can pulse open or closed. 2026 FEB 27 in lab book 
    MOT_coil_delay = 0.003 #Harvey said 3ms, I didn't test. 

    # --- Configure BBD301 stage ---
    #bbd301.move_to(1,147)
    xf_stage = 1  # move distance in mm (positive launches atoms up)
    v_stage = 5  # target velocity in mm/s
    a_stage = 10000  # acceleration in mm/s^2

    #calculate kinimatics
    t_accel = v_stage / a_stage  # time to reach target velocity
    d_accel = 0.5 * a_stage * t_accel**2  # distance covered during acceleration phase
    xi_stage = np.round((150 - d_accel - 0.25), 1)  # starting position of stage in mm, set so that it reaches target velocity as it hits the target position (with a bit of safety margin)
    print((xi_stage))
    if d_accel > abs(xf_stage - xi_stage):
        raise ValueError("Target velocity is too high for the given move distance and acceleration. Reduce velocity or increase acceleration.")

    #bbd301.move_to(1, xi_stage)  # move to starting position before the shot
    bbd301.set_velocity(1, v_stage)          # 0.015 m/s = 15 mm/s
    bbd301.set_acceleration(1, a_stage)    # 5000 mm/s^2, reaches 15 mm/s in 3 ms
    bbd301.set_move_distance(1, xf_stage)    # move distance on trigger (tune as needed)
    bbd301.set_reset_position(1, xi_stage)   # reset position after shot

    #do6363_0.go_high(t)

        
    # ============================================================
    # STEP 1-2: Reference photo with atoms trapped, beam on MRR
    # ============================================================
    add_time_marker(t, "Reference photo", verbose=True)
    my_ids_camera.expose(t=t, name='reference_image', frametype='atom', trigger_duration=1*ms)

    # STEP 3: Wait for camera refresh
    t += 10e-3

    # ============================================================
    # STEP 4: Close shutter 
    # ============================================================
    add_time_marker(t, "Close shutter", verbose=True)
    #MRR_SHUTTER_do.close(t) 
    t += 0.001 
    MRR_TRIG_do.go_high(t)
    MRR_TRIG_do.go_low(t + 1e-2)
    #MOT_COIL_do.go_low(t) # turn off MOT coils while shutter is closed to minimize free-fall time. Shutter takes 7 ms to close, coils take ~3 ms to fully turn off, so we wait 12 ms to ensure both are fully off before taking the next image. Tune timing as needed based on shutter timing and free-fall time.
    t += drop_time
    MRR_SHUTTER_do.open(t) # pulse shutter closed for min time to trigger on falling edge, then reopen. Tune timing as needed based on shutter timing and free-fall time.
    t+= 0.001 # wait 0.5 ms to ensure shutter is fully opened 
    my_ids_camera.expose(t=t, name='delayed image', frametype='atom', trigger_duration=1*ms) # take shot after shutter back on. 

    # STEP 5: Trigger MRR stage to start moving and wait until up to speed
    # We trigger now so the stage accelerates while the shutter is closed
    add_time_marker(t, "Trigger MRR stage", verbose=True)
    #MRR_TRIG_do.go_high(t)
    #MRR_TRIG_do.go_low(t + 1e-2)
    
    #we wait the greater of: (MRR delay + time to acclerate) or min time the shutter can pulse on
    t += max(t_accel + MRR_stage_delay, MRR_shutter_min_time)

    
    # ============================================================
    # STEP 6: Turn off MOT coils after shutter is fully closed
    # Shutter closed at t + 7 ms. Coil current takes ~3 ms to zero.
    # ============================================================
    #add_time_marker(t, "MOT coils off", verbose=True)
    #MOT_COIL_do.go_low(t - MOT_coil_delay)


    # PrawnBlaster pauses here until it receives a rising edge
    # from the BBD301 BNC 2 output (move complete signal).
    #wait("mrr_at_max_vel", t, timeout=.1)
    #t += 1e-3

    # ============================================================
    # STEP 7: Reopen shutter once stage is at full velocity
    # Stage reaches 15 mm/s after 3 ms. Shutter takes 7 ms to open.
    # ============================================================
    add_time_marker(t, "Reopen shutter", verbose=True)
    MRR_SHUTTER_do.open(t)
    #t+= 1e-3 # wait 1 ms to ensure shutter is fully open before taking image. Tune as needed based on shutter timing and free-fall time. 
    print(t)
    # ============================================================
    # STEP 8: Second camera exposure (optical molasses image)
    # ============================================================
    '''for i in range(5):
        add_time_marker(t, f"Molasses image {i}", verbose=True)
        my_ids_camera.expose(t, name=f'molasses_image {i}', frametype='atom', trigger_duration=1*ms)
        t += 0.05'''
        


    # ============================================================
    # Cleanup: turn off coil signal, etc.
    # ============================================================
    MOT_COIL_do.go_high(t)

    t += 0.75
    stop(t)