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
    t = 0
    t += dt

    # --- Configure BBD301 stage ---
    #bbd301.move_to(1,147)
    bbd301.set_velocity(1, 150)          # 0.015 m/s = 15 mm/s
    bbd301.set_acceleration(1, 5000)    # 5000 mm/s^2, reaches 15 mm/s in 3 ms
    bbd301.set_move_distance(1, -10)    # move distance on trigger (tune as needed)
    bbd301.set_reset_position(1, 147)   # reset position after shot
    '''
    t = 0.5
    for i in range(2):
        #do6363_0.go_low(0)
        
        MRR_SHUTTER_do.open(t)
        do6363_0.go_high(t)
        t += 0.005
        MRR_SHUTTER_do.close(t)  
        do6363_0.go_low(t)
        t+=.2

    '''
    MRR_SHUTTER_do.open(t)  # close shutter to start the sequence
    do6363_0.go_high(t) # trigger for testing, can be removed later
    t += 0.002
    MRR_TRIG_do.go_high(t)  # trigger for testing, can be removed later 







    t += dt
    stop(t)