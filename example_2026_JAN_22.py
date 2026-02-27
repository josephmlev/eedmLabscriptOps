import numpy as np
from labscript import *

#from labscriptlib.prawnTesting_JL_2026_JAN_6.connection_table import ct
from labscriptlib.eedmLabscriptOps.connection_table import ct

def switchToMotBeam():
    ao0.constant(t, 0)
    ao1.constant(t, 3)
    ao2.constant(t, 0)

def switchToMRRBeam():
    ao0.constant(t, 3)
    ao1.constant(t, 0)
    ao2.constant(t, 3)

if __name__ == "__main__":
    ct()  # call the connection table function to set up devices
    dt = 1e-2
    rate = 1/dt
    t = 0
    add_time_marker(t, "Start", verbose=True)
    start()

    t += dt
    ao0.constant(t, 0)
    my_ids_camera.expose(t=t, name='first_image', frametype='atom', trigger_duration=100*ms)
    MOT_SHUTTER_do.go_high(t)


    t += 100 * dt
    add_time_marker(t, "Set AO0 to 3V", verbose=True)   
    ao0.constant(t, 3)
    MOT_SHUTTER_do.go_low(t)

    t += 100 * dt
    add_time_marker(t, "Set AO0 to 0V", verbose=True)   
    ao0.constant(t, 0)
    ai0.acquire(start_time = t, end_time = t + 200*dt, label = 'test_ai0')

      # --- INSERTED WAIT HERE ---
    # The PrawnBlaster will pause here. It resumes execution if it receives 
    # a rising edge on the external trigger input (Default: GPIO 0), 
    # or if the 'timeout' (in seconds) expires.
    #add_time_marker(t, "wait here!")
    wait("wait", t, timeout=1)
    t += dt
    # --------------------------

    switchToMotBeam()
    t+=100 * dt
    switchToMRRBeam()
    t += 100 * dt
    add_time_marker(t, "Set AO0 to 3V", verbose=True)   
    ao0.constant(t, 3)

    t += 100 * dt
    add_time_marker(t, "Set AO0 to 0V", verbose=True)   
    ao0.constant(t, 0)

    t += dt
    
    '''
    DO0.go_high(t+dt)
    
    t+= 100 *dt
    
    add_time_marker(t, "DO0 go high", verbose=True)
    DO0.go_low(t)

    t += 100 * dt
    
    add_time_marker(t, "do2 go high")
    
    DO0.go_high(t)
    t += 100 * dt
    DO0.go_low(t)
    t += 100 * dt
    DO0.go_high(t)
    DO1.go_high(t)
    t += 100 * dt
  
    # --- INSERTED WAIT HERE ---
    # The PrawnBlaster will pause here. It resumes execution if it receives 
    # a rising edge on the external trigger input (Default: GPIO 0), 
    # or if the 'timeout' (in seconds) expires.
    #add_time_marker(t, "wait here!")
    wait("wait", t, timeout=5)
    t += dt
    # --------------------------

    DO0.go_low(t)
    DO1.go_low(t)

    t += 200 * dt
    
    DO0.go_high(t)
    
    t += 10*dt
    '''

    stop(t)
