# Test: Photon Counter Acquisition

from labscript import *
from labscriptlib.eedmLabscriptOps.connection_table import ct

if __name__ == "__main__":
    ct()
    start()

    REPUMP_SHUTTER_do.open(t=0) 
    scope_trig_do.go_low(t=0) 
    # Starting at 1.0 sec, take samples. 100 kHz sample rate is hardcoded
    photon_counter.acquire(t=.1, number_of_counts=int(5e5))


    # Make sure we start low so edge counts are clean.
    scope_trig_do.go_low(t=0)

    if 0: #use scope trig do to generate pulses:
        # Minimum half-period: 10 us high + 10 us low = 20 us per pulse.
        HALF = 10e-6
            # Clock resolution. Snap all edge times to this grid to avoid
        # floating-point accumulation landing just under the 10us minimum.
        DT = 10e-6

        def snap(x):
            return round(x / DT) * DT

        # ============================================================
        # Region 1 (0.00 - 0.20 s): steady slow pulse train.
        # 1 kHz => 500 us high, 500 us low. Easy to count by eye.
        # Cumulative should rise as a straight line; diff = constant.
        # ============================================================
        t = 0.0
        period = 1e-3  # 1 kHz
        while t < 0.20 - period:
            scope_trig_do.go_high(t)
            scope_trig_do.go_low(t + period / 2)
            t += period

        # ============================================================
        # Region 2 (0.20 - 0.30 s): nothing. Flat line.
        # Cumulative stays flat; diff = 0. Sanity check for "no counts".
        # ============================================================
        scope_trig_do.go_low(0.20)

        # ============================================================
        # Region 3 (0.30 - 0.50 s): increasing rate (frequency ramp).
        # Floor the period at 40 us (not 20 us) so high+low each stay
        # comfortably above the 10 us clock resolution after rounding.
        # ============================================================
        t = 0.30
        n = 0
        while t < 0.50:
            period = max(2e-3 * (1 - n / 120.0), 4 * HALF)  # floor = 40 us
            hi = snap(t)
            lo = snap(t + period / 2)
            if lo <= hi:           # guard against zero-width pulse
                lo = hi + DT
            scope_trig_do.go_high(hi)
            scope_trig_do.go_low(lo)
            t += period
            n += 1

        # ============================================================
        # Region 6 (0.90 - 1.00 s): silent again. Flat to the end.
        # ============================================================
        scope_trig_do.go_low(0.90)

    REPUMP_SHUTTER_do.close(t=5.0)
    stop(5.001)
