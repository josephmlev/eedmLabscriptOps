# Experiment: Ruler calibration image
# Take a single picture and save a note to the h5 file.
# Put the ruler at different distances, change the note each time.

from labscript import *
from labscriptlib.eedmLabscriptOps.connection_table import ct

if __name__ == "__main__":
    ct()
    start()

    t = 0

    # Globals with defaults
    try:
        note
    except NameError:
        note = '110mm'

    try:
        ruler_distance_mm
    except NameError:
        ruler_distance_mm = 0.0

    # Save note and distance to h5
    add_time_marker(t, "Start", verbose=True)

    t += 0.01

    my_ids_camera.expose(
        t=t, name='ruler', frametype='atom',
        trigger_duration=1*ms
    )

    t += 0.1
    stop(t)