import nidaqmx
import numpy as np
import matplotlib.pyplot as plt
import pyvisa
from datetime import datetime
import time
import os

# ---------- Configuration ----------
SCOPE_VISA = "USB0::0x1AB1::0x0610::HDO1B275M00060::INSTR"  # <-- put your scope's VISA address here
TRIGGER_LINE = "PXI1Slot2/port0/line4"  #line to trigger stage
SAVE_DIR = r"C:\Users\eedm\labscript-suite\userlib\labscriptlib\eedmLabscriptOps\controlsAndMotDiagnosticAndLaunchTest_3_10_26\mrrVelocityBeatNote\data"  # <-- where to save

# ---------- Configuration ----------
PD_CHANNEL = 4       # photodiode beat signal

# Vertical settings per channel
PD_SCALE = 10e-3      # 5 mV/div for the beat
PD_OFFSET = 0.0
PD_COUPLING = "DC"

# Scope time acquisition settings
SAMPLE_RATE = 50e6  #samples per sec        
RECORD_LENGTH = int(10e6)    # 50 Mpts max
TIMEBASE = 20e-3             # 10 ms/div -> 100 ms total window


TRIGGER_PULSE_WIDTH = 0.01   # 10 ms TTL high


# ---------- Scope control ----------
def setup_scope(scope):
    """Configure scope for single-shot deep-memory acquisition."""
    scope.timeout = 30000  # ms
    scope.write("*RST")
    time.sleep(1.0)
    scope.write("*CLS")

        # Photodiode channel
    scope.write(f":CHAN{PD_CHANNEL}:DISP ON")
    scope.write(f":CHAN{PD_CHANNEL}:COUP {PD_COUPLING}")
    scope.write(f":CHAN{PD_CHANNEL}:SCAL {PD_SCALE}")
    scope.write(f":CHAN{PD_CHANNEL}:OFFS {PD_OFFSET}")

    # Turn off all other channels (max memory on PD channel)
    for ch in [1, 2, 3]:
        if ch != PD_CHANNEL:
            scope.write(f":CHAN{ch}:DISP OFF")


    # Trigger on EXT input
    scope.write(":TRIG:MODE EDGE")
    scope.write(":TRIG:EDGE:SOUR EXT")
    scope.write(":TRIG:EDGE:SLOP POS")
    scope.write(":TRIG:EDGE:LEV 1.5")
    scope.write(":TRIG:SWE SING")
    

    # Timebase
    scope.write(f":TIM:SCAL {TIMEBASE}")
    scope.write(":TIM:OFFS 0.090")  # 49 ms, trigger sits at -1 ms from left edge of post-trigger region

    # Acquisition: deep memory, single shot
    scope.write(":ACQ:TYPE NORM")
    scope.write(f":ACQ:MDEP {RECORD_LENGTH}")


    # Confirm settings
    actual_sr = float(scope.query(":ACQ:SRAT?"))
    actual_md = float(scope.query(":ACQ:MDEP?"))
    print(f"Scope sample rate: {actual_sr/1e6:.1f} MSa/s")
    print(f"Scope memory depth: {actual_md/1e6:.1f} Mpts")
    print(f"Record duration: {actual_md/actual_sr*1e3:.1f} ms")

    return actual_sr, actual_md


def arm_scope(scope):
    """Arm the scope for a single acquisition."""
    scope.write(":SING")
    time.sleep(0.2)  # let it actually arm before triggering


def wait_for_acquisition(scope, timeout=30):
    """Block until acquisition completes."""
    t0 = time.time()
    while time.time() - t0 < timeout:
        status = scope.query(":TRIG:STAT?").strip()
        if status == "STOP":
            return True
        time.sleep(0.05)
    raise TimeoutError("Scope did not finish acquisition")


def fetch_waveform(scope):
    """Pull the waveform off the scope as a numpy array of voltages + time axis."""
    scope.write(f":WAV:SOUR CHAN{PD_CHANNEL}")
    scope.write(":WAV:MODE RAW")
    scope.write(":WAV:FORM BYTE")

    # Get scaling parameters
    preamble = scope.query(":WAV:PRE?").strip().split(",")
    x_inc = float(preamble[4])
    x_orig = float(preamble[5])
    y_inc = float(preamble[7])
    y_orig = float(preamble[8])
    y_ref = float(preamble[9])

    # Read in chunks (scope has a max points-per-read limit)
    total_pts = int(float(scope.query(":ACQ:MDEP?")))
    chunk = 1_000_000
    raw = np.empty(total_pts, dtype=np.uint8)

    for start in range(0, total_pts, chunk):
        stop = min(start + chunk, total_pts)
        scope.write(f":WAV:STAR {start+1}")
        scope.write(f":WAV:STOP {stop}")
        data = scope.query_binary_values(":WAV:DATA?", datatype="B", container=np.array)
        raw[start:stop] = data
        print(f"  fetched {stop}/{total_pts} pts", end="\r")
    print()

    voltages = (raw.astype(np.float32) - y_ref - y_orig) * y_inc
    times = x_orig + np.arange(total_pts) * x_inc
    return times, voltages


# ---------- NI trigger ----------
def send_trigger_pulse():
    """Send a single TTL pulse on the configured DO line."""
    with nidaqmx.Task() as task:
        task.do_channels.add_do_chan(TRIGGER_LINE)
        task.write(True)
        time.sleep(TRIGGER_PULSE_WIDTH)
        task.write(False)


# ---------- Saving ----------
def save_data(times, voltages, sample_rate):
    os.makedirs(SAVE_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = os.path.join(SAVE_DIR, f"beat_{timestamp}.npz")
    np.savez_compressed(
        fname,
        times=times,
        voltages=voltages,
        sample_rate=sample_rate,
        timestamp=timestamp,
    )
    print(f"Saved {fname}  ({voltages.nbytes/1e6:.1f} MB raw)")
    return fname


# ---------- Plotting ----------
def plot_waveform(times, voltages):
    # Decimate for plotting if very long
    n = len(voltages)
    decim = max(1, n // 200_000)
    t_plot = times[::decim] * 1e3  # ms
    v_plot = voltages[::decim] * 1e3  # mV

    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(t_plot, v_plot, lw=0.5)
    ax.set_xlabel("Time (ms)")
    ax.set_ylabel("Beat signal (mV)")
    ax.set_title(f"Beat note, {n/1e6:.1f} Mpts")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    plt.show()


# ---------- Main ----------
def main():
    print("Connecting to scope...")
    rm = pyvisa.ResourceManager()
    scope = rm.open_resource(SCOPE_VISA)
    print(f"Connected: {scope.query('*IDN?').strip()}")

    try:
        setup_scope(scope)

        input("Set up Kinesis stage and press Enter to arm scope and trigger...")

        print("Arming scope...")
        arm_scope(scope)

        print("Force-triggering to prime scope...")
        scope.write(":TFOR")
        time.sleep(0.5)

        # Re-arm for the real shot
        print("Re-arming scope for real trigger...")
        arm_scope(scope)

        print("Waiting 1 s before sending trigger...")
        time.sleep(1.0)

        print("Sending trigger pulse...")
        send_trigger_pulse()

        print("Waiting for acquisition...")
        wait_for_acquisition(scope, timeout=30)

        sr = float(scope.query(":ACQ:SRAT?"))
        md = float(scope.query(":ACQ:MDEP?"))
        print(f"Actual sample rate: {sr/1e6:.3f} MSa/s,  memory depth: {md/1e6:.3f} Mpts")

        print("Fetching waveform...")
        times, voltages = fetch_waveform(scope)

        fname = save_data(times, voltages, sr)
        plot_waveform(times, voltages)

    finally:
        scope.close()
        rm.close()

if __name__ == "__main__":
    main()