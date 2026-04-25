from labscript import *
from labscriptlib.eedmLabscriptOps.connection_table import ct

def set_beam_path(t, mode):
    """Switch beam path between 'MOT' and 'MRR'.
    
    MOT: MOT shutter open, MRR shutter closed, all LCRs to V1
    MRR: MOT shutter closed, MRR shutter open, all LCRs to V2
    """
    if mode == 'MOT':
        MOT_SHUTTER_do.open(t)
        MRR_SHUTTER_do.close(t)
        LCR_do.go_low(t)
        LCR_BOT_do.go_low(t)
        LCR_HOR_ao.constant(t, 0.0)
        LCR_TOP_ao.constant(t, 0.0)
    elif mode == 'MRR':
        MOT_SHUTTER_do.close(t)
        MRR_SHUTTER_do.open(t)
        LCR_do.go_high(t)
        LCR_BOT_do.go_high(t)
        LCR_HOR_ao.constant(t, 5.0)
        LCR_TOP_ao.constant(t, 5.0)
    else:
        raise ValueError(f"Unknown beam path mode: {mode}. Use 'MOT' or 'MRR'.")

if __name__ == "__main__":
    ct()
    start()

    t = 0
    '''
    MOT_COIL_do.go_low(t)

    # First pulse
    t = 10e-3
    MOT_COIL_do.go_high(t)
    #t += 1e-3
    #MOT_COIL_do.go_low(t)

    # Second pulse 1 second later
    t += 1.0*1.001
    MOT_COIL_do.go_low(t)
    #t += 1e-3
    #MOT_COIL_do.go_low(t)
    '''

    
    set_beam_path(t, 'MOT')   # switch to MOT arm
    t+=3
    set_beam_path(t, 'MRR')   # switch to MRR arm
    t+=3
    set_beam_path(t, 'MOT')   # switch to MOT arm
    t+=3
    set_beam_path(t, 'MRR')   # switch to MRR arm
    t+=3
    set_beam_path(t, 'MOT')   # switch to MOT arm
    t+=3
    set_beam_path(t, 'MRR')   # switch to MRR arm
    t+=3
    set_beam_path(t, 'MOT')   # switch to MOT arm


    t += 10e-3
    stop(t)