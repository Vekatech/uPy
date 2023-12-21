import gc
import random
import network
from os import uname
from machine import Pin
from umodbus.tcp import ModbusTCP

BRD = uname().machine

# Configure digital inputs and outputs

def coil_set_cb(reg_type, address, val):
    #print('Custom callback, called on setting {} at {} to: {}'.format(reg_type, address, val))
    
    for idx, c in enumerate(val):
        if c:
            LEDs[address+idx].on()
        else:
            LEDs[address+idx].off()

#def coil_get_cb(reg_type, address, val):
#    print('Custom callback, called on getting {} at {}, currently: {}'.format(reg_type, address, val))

#def discrete_get_cb(reg_type, address, val):
#    print('Custom callback, called on getting {} at {}, currently: {}'.format(reg_type, address, val))

if("VK-RA6M3" in BRD):
    LEDs = [Pin('LED_R', Pin.OUT), Pin('LED_G', Pin.OUT), Pin('LED_B', Pin.OUT), Pin('LED_Y', Pin.OUT)]
    BTNs = [Pin('P008', Pin.IN), Pin('P009', Pin.IN)]

    register_definitions = {
        "COILS": {
            "LEDs": {
                "register": 0,
                "len": 4,
                "val": [0, 0, 0, 0],
                "on_set_cb": coil_set_cb
            }
        },
        "HREGS": {
            "EXAMPLE_HREG": {
                "register": 100,
                "len": 3,
                "val": [19, 30, 40]
            }
        },
        "ISTS": {
            "BTNs": {
                "register": 0,
                "len": 2,
                "val": [0, 0]
            }
        },
        "IREGS": {
            "EXAMPLE_IREG": {
                "register": 10,
                "len": 2,
                "val": [60001, 5000]
            }
        }
    }
elif("VK-RA6M5" in BRD):
    LEDs = [Pin('LED_R', Pin.OUT), Pin('LED_G', Pin.OUT), Pin('LED_B', Pin.OUT)]
    BTNs = [Pin('P010', Pin.IN), Pin('P009', Pin.IN)]

    register_definitions = {
        "COILS": {
            "LEDs": {
                "register": 0,
                "len": 3,
                "val": [0, 0, 0],
                "on_set_cb": coil_set_cb
            }
        },
        "HREGS": {
            "EXAMPLE_HREG": {
                "register": 100,
                "len": 3,
                "val": [19, 30, 40]
            }
        },
        "ISTS": {
            "BTNs": {
                "register": 0,
                "len": 2,
                "val": [0, 0]
            }
        },
        "IREGS": {
            "EXAMPLE_IREG": {
                "register": 10,
                "len": 2,
                "val": [60001, 5000]
            }
        }
    }

def UP():
    # network connections shall be made here, check the MicroPython port specific
    # documentation for connecting to or creating a network
    
    # TCP Client/Slave setup
    # set IP address of this MicroPython device explicitly
    # local_ip = '192.168.4.1'  # IP address
    # or get it from the system after a connection to the network has been made
    # it is not the task of this lib to provide a detailed explanation for this
    Lan = network.LAN()
    print('Taking an IP ...')
    Lan.active(True)
    print('Got {} from DHCP'.format(Lan.ifconfig()[0]))
    
    MBclient = ModbusTCP()
    
    # check whether client has been bound to an IP and a port
    if not MBclient.get_bound_status():
        MBclient.bind(local_ip=Lan.ifconfig()[0], local_port=502)

    # use the defined values of each register type provided by register_definitions
    MBclient.setup_registers(registers=register_definitions)

    while True:
        try:
            for idx, btn in enumerate(BTNs):
                v = btn.value()
                if MBclient.get_ist(idx) != v:
                    MBclient.set_ist(idx, v)

            result = MBclient.process()

        except KeyboardInterrupt:
            print('KeyboardInterrupt, stopping TCP client...')
            break
        except Exception as e:
            print('Exception during execution: {}'.format(e))
