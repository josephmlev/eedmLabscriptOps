import nidaqmx

# Configuration dictionary
# Digital channels: True = High, False = Low
# Analog channels: 5.0 = High, 0.0 = Low
BEAM_CONFIGS = {
    "MOT": {
        "digital": {
            "PXI1Slot2/port0/line5": True,   #MOT shutter open
            "PXI1Slot2/port0/line6": False,   #MRR shutter closed
            "PXI1Slot2/port0/line7": False,   #LCR switch set to V2 (MOT)
            "PXI1Slot2/port0/line2": False    #Bottom LCR set to V2 (MOT)
        },
        "analog": {
            "PXI1Slot2/ao0": 0.0, #hor LCR set to V2 (MOT)
            "PXI1Slot2/ao1": 0.0, #top LCR set to V2 (MOT)
        },
    },
    "MRR": {
        "digital": {
            "PXI1Slot2/port0/line5": False,   #MOT shutter closed
            "PXI1Slot2/port0/line6": True,    #MRR shutter open
            "PXI1Slot2/port0/line7": True,    #LCR set to V1 (MRR)
            "PXI1Slot2/port0/line2": True     #Bottom LCR set to V1 (MRR)
        },
        "analog": {
            "PXI1Slot2/ao0": 5.0, #hor LCR set to V1 (MRR)
            "PXI1Slot2/ao1": 5.0, #top LCR set to V1 (MRR)
        },
    },
}

# Starting beam state
current_beam = "MRR"


def set_beam(config_name):
    config = BEAM_CONFIGS[config_name]

    # Write digital outputs
    with nidaqmx.Task() as task:
        for channel in config["digital"]:
            task.do_channels.add_do_chan(channel)
        task.write(list(config["digital"].values()))

    # Write analog outputs
    with nidaqmx.Task() as task:
        for channel in config["analog"]:
            task.ao_channels.add_ao_voltage_chan(channel, min_val=0.0, max_val=5.0)
        task.write(list(config["analog"].values()))


def main():
    global current_beam

    # Set initial state
    set_beam(current_beam)
    print(f"Beam set to {current_beam}")

    while True:
        try:
            input("Press Enter to toggle beam (Ctrl+C to quit)...")
        except KeyboardInterrupt:
            print("\nExiting.")
            break

        current_beam = "MOT" if current_beam == "MRR" else "MRR"
        set_beam(current_beam)
        print(f"Beam set to {current_beam}")


if __name__ == "__main__":
    main()