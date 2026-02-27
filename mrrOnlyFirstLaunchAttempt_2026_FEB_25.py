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

    dt = 1e-2  # 10 ms base time step
    t = 0.01 # start 10 ms after t=0 to give shutter delay time to be included.
    MRR_stage_delay = 5e-3  # time for stage to reach full velocity, based on acceleration and target velocity

    # --- Configure BBD301 stage ---
    #bbd301.move_to(1,147)
    bbd301.set_velocity(1, 300)          # 0.015 m/s = 15 mm/s
    bbd301.set_acceleration(1, 5000)    # 5000 mm/s^2, reaches 15 mm/s in 3 ms
    bbd301.set_move_distance(1, -30)    # move distance on trigger (tune as needed)
    bbd301.set_reset_position(1, 147)   # reset position after shot

    #do6363_0.go_high(t)
    
    MOT_COIL_do.go_high(t)  # turn on MOT coils. Should already be on from last time!
    MRR_TRIG_do.go_low(t) 
    MRR_SHUTTER_do.open(t)
    do6363_0.go_low(t)  # trigger for testing, remove later

    # ============================================================
    # STEP 1-2: Reference photo with atoms trapped, beam on MRR
    # ============================================================
    add_time_marker(t, "Reference photo", verbose=True)
    #my_ids_camera.expose(t=t, name='reference_image', frametype='atom', trigger_duration=1*ms)

    # STEP 3: Wait for camera refresh
    t += 10e-3

    # ============================================================
    # STEP 4: Close shutter 
    # ============================================================
    add_time_marker(t, "Close shutter", verbose=True)
    MRR_SHUTTER_do.close(t)  

    # STEP 5: Trigger MRR stage to start moving and wait until up to speed
    # We trigger now so the stage accelerates during the 7 ms shutter close time.
    # At 5000 mm/s^2 it reaches 15 mm/s in 3 ms, so it's at full speed
    # before the shutter finishes closing.
    add_time_marker(t, "Trigger MRR stage", verbose=True)
    MRR_TRIG_do.go_high(t)
    MRR_TRIG_do.go_low(t + 1e-2)
    #MRR_TRIG_do.go_high(t + 1.1e-2)
    #MRR_TRIG_do.go_low(t + 1.2e-2)


    '''
    # ============================================================
    # STEP 6: Turn off MOT coils after shutter is fully closed
    # Shutter closed at t + 7 ms. Coil current takes ~3 ms to zero.
    # ============================================================
    add_time_marker(t_shutter_closed, "MOT coils off", verbose=True)
    MOT_COIL_do.go_low(t_shutter_closed)  

    # PrawnBlaster pauses here until it receives a rising edge
    # from the BBD301 BNC 2 output (move complete signal).
    wait("mrr_at_max_vel", t, timeout=.1)
    t += 1e-3

    # ============================================================
    # STEP 7: Reopen shutter once stage is at full velocity
    # Stage reaches 15 mm/s after 3 ms. Shutter takes 7 ms to open.
    # So we trigger reopen early: we want it open by ~t + 10 ms,
    # meaning we send the open signal at ~t + 3 ms.
    # But shutter only just started closing at t, so let's wait
    # until it's fully closed first, then reopen.
    # Free-fall time = shutter closed duration. Minimize this.
    # ============================================================
    t_reopen_shutter = t_shutter_closed + 1e-3  # open command 1 ms after closed, 
                                                  # shutter takes 7 ms to actually open
                                                  # so atoms in free fall for ~8 ms total
    add_time_marker(t_reopen_shutter, "Reopen shutter", verbose=True)
    MRR_SHUTTER_do.open(t_reopen_shutter)

    # ============================================================
    # STEP 8: Second camera exposure (optical molasses image)
    # Shutter fully open ~7 ms after reopen command
    # ============================================================
    t_shutter_open = t_reopen_shutter + 7e-3
    add_time_marker(t_shutter_open, "Molasses image", verbose=True)
    my_ids_camera.expose(t=t_shutter_open, name='molasses_image', frametype='atom', trigger_duration=10*ms)

    # Let the exposure finish
    t = t_shutter_open + 20e-3

    # ============================================================
    # Cleanup: turn off coil signal, etc.
    # ============================================================
    MOT_COIL_do.go_high(t)'''

    t += 2*dt
    stop(t)