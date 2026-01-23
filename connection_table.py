
from labscript import *
from labscript import AnalogOut
from labscript_devices.DummyPseudoclock.labscript_devices import DummyPseudoclock
from labscript_devices.DummyIntermediateDevice import DummyIntermediateDevice
from labscript_devices.NI_DAQmx.models.NI_PXIe_6738 import NI_PXIe_6738
from labscript_devices.NI_DAQmx.models.NI_PXIe_6363 import NI_PXIe_6363
from labscript_devices.IMAQdxCamera.labscript_devices import IMAQdxCamera
from labscript_devices.PrawnBlaster.labscript_devices import PrawnBlaster

#from labscript_devices import IDS_PeakCamera
from user_devices.IDS_PeakCamera.labscript_devices import IDS_PeakCamera
def ct():
    PrawnBlaster(
        name                = 'prawn', 
        com_port            = 'COM10', 
        num_pseudoclocks    = 1,
        pico_board          = 'pico2'
    )

    SLOT_6738 = "PXI1Slot3"   # EXACT name from NI-MAX
    SLOT_6363 = "PXI1Slot2"   # EXACT name from NI-MAX

    NI_PXIe_6738(
        name                    = 'NI6738',
        parent_device           = prawn.clocklines[0],
        MAX_name                = SLOT_6738,
        clock_terminal          = '/PXI1Slot3/PFI0',         # <-- empty string means "use internal/Onboard clock"
        max_AO_sample_rate      = 100000.00000000001,
    )

    NI_PXIe_6363(
        name                    = 'NI6363',
        parent_device           = prawn.clocklines[0],
        MAX_name=SLOT_6363,
        clock_terminal          = '/PXI1Slot2/PFI12',         # <-- empty string means "use internal/Onboard clock"
        acquisition_rate=100.0
    )

    # Define digital outs on 6363
    #make sure to define an even number of channels for Labscript to be happy
    DigitalOut(name='do6363_0', parent_device=NI6363, connection='port0/line0')
    DigitalOut(name='do6363_1', parent_device=NI6363, connection='port0/line1')
    DigitalOut(name='do6363_2', parent_device=NI6363, connection='port0/line2')
    DigitalOut(name='do6363_3', parent_device=NI6363, connection='port0/line3')
    DigitalOut(name='do6363_4', parent_device=NI6363, connection='port0/line4')
    DigitalOut(name='MOT_SHUTTER_do', parent_device=NI6363, connection='port0/line5')
    DigitalOut(name='MRR_SHUTTER_do', parent_device=NI6363, connection='port0/line6')
    DigitalOut(name='LCR_do', parent_device=NI6363, connection='port0/line7')

    # Define analog outs on 6738
    # Make sure to define an even number of channels for Labscript to be happy
    AnalogOut(name='ao0', parent_device=NI6738, connection='ao0')
    AnalogOut(name='ao1', parent_device=NI6738, connection='ao1')
    AnalogOut(name='ao2', parent_device=NI6738, connection='ao2')
    AnalogOut(name='ao3', parent_device=NI6738, connection='ao3')
    AnalogOut(name='ao4', parent_device=NI6738, connection='ao4')
    AnalogOut(name='ao5', parent_device=NI6738, connection='ao5')
    AnalogOut(name='ao6', parent_device=NI6738, connection='ao6')
    AnalogOut(name='ao7', parent_device=NI6738, connection='ao7')

    # Define analog ins on 6363
    AnalogIn(name='ai0', parent_device=NI6363, connection='ai0')
    AnalogIn(name='ai1', parent_device=NI6363, connection='ai1')

    # Again, make sure to define an even number of channels for Labscript to be happy
    #do0 = DigitalOut('do0', ao6738, 'port0/line1')
    DigitalOut('do1_dummy', NI6738, 'port0/line0')  # dummy to make even number of digital lines


    cam = IDS_PeakCamera(
        name='my_ids_camera',
        parent_device=NI6738,
        connection='port0/line1', 
        serial_number='4108596607', #sn yellow 4103389953 blue 4108596607 red 4108596608
        minimum_recovery_time=0.005, # Override the default
        trigger_edge_type='rising', # We will trigger via software
        trigger_duration=0.05,
        camera_attributes={
            'trigger': 'On', # On/Off
            'format': 'Mono8', # Mono8/Mono12
            'exposure': 1.0, # 9 ms, using the wrapper property
            'fps': 5.0,   # required by base class (will be skipped at runtime)
            'gain': 1.0
        },
        manual_mode_camera_attributes={ # BLACS preview mode
            "trigger": "Off",
            "format": "Mono8",
            "exposure": 1.0,
            "fps": 5.0,               # shown in BLACS, not applied to hardware
            "gain": 1.0,
        },
    )


if __name__ == '__main__':
    ct()
    start()
    stop(1)