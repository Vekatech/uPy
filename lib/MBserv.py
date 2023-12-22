import json
import network
from os import uname
from machine import Pin, ADC, DAC
from umodbus.tcp import ModbusTCP

BRD = uname().machine

# Configure digital inputs and outputs

def coil_set_cb(reg_type, address, val):
    for idx, c in enumerate(val):
        if c:
            LEDs[address+idx].on()
        else:
            LEDs[address+idx].off()

def reg_set_cb(reg_type, address, val):
    for AOn, r in enumerate(val):
        DACs[address+AOn].write(r)

def pcfg_set_cb(reg_type, address, val):
    for i in range(0, 13):
        if val[0] & (1 << i):
            PINs[i] = Pin('D{}'.format(i), Pin.IN)
        else:
            PINs[i] = Pin('D{}'.format(i), Pin.OUT)

def pin_set_cb(reg_type, address, val):
    for p in range(0, 13):
        if val[0] & (1 << p):
            PINs[p].on()
        else:
            PINs[p].off()

#def coil_get_cb(reg_type, address, val):
#    print('Custom callback, called on getting {} at {}, currently: {}'.format(reg_type, address, val))

#def discrete_get_cb(reg_type, address, val):
#    print('Custom callback, called on getting {} at {}, currently: {}'.format(reg_type, address, val))

PINs = [Pin('D0', Pin.IN), Pin('D1', Pin.IN), Pin('D2', Pin.IN), Pin('D3', Pin.IN), Pin('D4', Pin.IN), Pin('D5', Pin.IN), Pin('D6', Pin.IN), Pin('D7', Pin.IN), Pin('D8', Pin.IN), Pin('D9', Pin.IN), Pin('D10', Pin.IN), Pin('D11', Pin.IN), Pin('D12', Pin.IN), Pin('D13', Pin.IN)]
ADCs = [ADC('A0'), ADC('A1'), ADC('A2'), ADC('A3')]
DACs = [DAC('A4'), DAC('A5')]

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
            "DACs": {
                "register": 0,
                "len": 2,
                "val": [0, 0],
                "on_set_cb": reg_set_cb
            },
            "PINcfg": {
                "register": 2,
                "len": 1,
                "val": 0x3FFF,
                "on_set_cb": pcfg_set_cb
            },
            "PINout": {
                "register": 3,
                "len": 1,
                "val": 0,
                "on_set_cb": pin_set_cb
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
            "ADCs": {
                "register": 0,
                "len": 4,
                "val": [0, 0, 0, 0]
            },
            "PINin": {
                "register": 4,
                "len": 1,
                "val": 0
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
            "DACs": {
                "register": 0,
                "len": 2,
                "val": [0, 0],
                "on_set_cb": reg_set_cb
            },
            "PINcfg": {
                "register": 2,
                "len": 1,
                "val": 0x3FFF,
                "on_set_cb": pcfg_set_cb
            },
            "PINout": {
                "register": 3,
                "len": 1,
                "val": 0,
                "on_set_cb": pin_set_cb
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
            "ADCs": {
                "register": 0,
                "len": 4,
                "val": [0, 0, 0, 0]
            },
            "PINin": {
                "register": 4,
                "len": 1,
                "val": 0
            }
        }
    }

def UP(conf = 'Settings.json'):
    # network connections shall be made here, check the MicroPython port specific
    # documentation for connecting to or creating a network
    
    # TCP Client/Slave setup
    # set IP address of this MicroPython device explicitly
    # local_ip = '192.168.4.1'  # IP address
    # or get it from the system after a connection to the network has been made
    # it is not the task of this lib to provide a detailed explanation for this

    try:
        with open('/flash/' + conf, 'r') as file:
            settings = json.load(file)
    except Exception as e:
        settings = None
        print("<file> [{}]:".format(type(e).__name__), e)

    Lan = network.LAN()
    if settings is not None:
        Lan.config(mac=bytes.fromhex(settings['ETH']['MAC']))
    
    print('Taking an IP ...')
    Lan.active(True)
    print('Got {} from DHCP'.format(Lan.ifconfig()[0]))
    
    MBclient = ModbusTCP()
    
    # check whether client has been bound to an IP and a port
    if not MBclient.get_bound_status():
        MBclient.bind(Lan.ifconfig()[0], settings['MB']['port'] if settings is not None else 502)

    # use the defined values of each register type provided by register_definitions
    MBclient.setup_registers(registers=register_definitions)

    while True:
        try:
            for Bn, btn in enumerate(BTNs):
                v = btn.value()
                if MBclient.get_ist(Bn) != v:
                    MBclient.set_ist(Bn, v)

            for An, adc in enumerate(ADCs):
                MBclient.set_ireg(An, adc.read_u16())

            Din = 0
            for Dn in range(0, 13):
                if PINs[Dn].value():
                    Din += (1 << Dn)

            MBclient.set_ireg(4, Din)

            result = MBclient.process()

        except KeyboardInterrupt:
            print('KeyboardInterrupt, stopping TCP client...')
            break
        except Exception as e:
            print('Exception during execution: {}'.format(e))
