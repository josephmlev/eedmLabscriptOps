# Experiment: Photodiode trigger test
# Opens MRR shutter, waits for external trigger on prawnblaster,
# then pulses repump rel jump to trigger scope.

from labscript import *
from labscriptlib.eedmLabscriptOps.connection_table import ct

if __name__ == "__main__":
    ct()
    start()

    t = 0

    # Everything off
    MOT_COIL_do.go_low(t)
    MRR_SHUTTER_do.close(t)
    MOT_SHUTTER_do.close(t)
    REPUMP_SHUTTER_do.close(t)
    MAIN_REL_JUMP_do.go_low(t)
    REPUMP_REL_JUMP_do.go_low(t)
    LCR_do.go_high(t)

    t += 0.01

    # Open MRR shutter
    MRR_SHUTTER_do.open(t)

    #t += 0.01

    # Wait for photodiode trigger, 5 second timeout
    wait("pd_trigger", t, timeout=5)
    t += 0.00

    # Trigger received -- pulse repump rel jump to trigger scope
    REPUMP_REL_JUMP_do.go_high(t)

    t += 0.1

    # Cleanup
    REPUMP_REL_JUMP_do.go_low(t)
    MRR_SHUTTER_do.close(t)

    t += 0.01
    stop(t)