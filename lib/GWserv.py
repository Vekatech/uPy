import time
import json
import struct
import random
import socket
import network
import asyncio
from os import uname
from machine import Pin, UART
#from microdot import Microdot
from microdot_asyncio import Microdot

# Protocol Data Unit (PDU) constants
#: CRC length
CRC_LENGTH = const(0x02)
#: Modbus Application Protocol High Data Response length
MBAP_HDR_LENGTH = const(0x07)

#: CRC16 lookup table
CRC16_TABLE = (
    0x0000, 0xC0C1, 0xC181, 0x0140, 0xC301, 0x03C0, 0x0280, 0xC241, 0xC601,
    0x06C0, 0x0780, 0xC741, 0x0500, 0xC5C1, 0xC481, 0x0440, 0xCC01, 0x0CC0,
    0x0D80, 0xCD41, 0x0F00, 0xCFC1, 0xCE81, 0x0E40, 0x0A00, 0xCAC1, 0xCB81,
    0x0B40, 0xC901, 0x09C0, 0x0880, 0xC841, 0xD801, 0x18C0, 0x1980, 0xD941,
    0x1B00, 0xDBC1, 0xDA81, 0x1A40, 0x1E00, 0xDEC1, 0xDF81, 0x1F40, 0xDD01,
    0x1DC0, 0x1C80, 0xDC41, 0x1400, 0xD4C1, 0xD581, 0x1540, 0xD701, 0x17C0,
    0x1680, 0xD641, 0xD201, 0x12C0, 0x1380, 0xD341, 0x1100, 0xD1C1, 0xD081,
    0x1040, 0xF001, 0x30C0, 0x3180, 0xF141, 0x3300, 0xF3C1, 0xF281, 0x3240,
    0x3600, 0xF6C1, 0xF781, 0x3740, 0xF501, 0x35C0, 0x3480, 0xF441, 0x3C00,
    0xFCC1, 0xFD81, 0x3D40, 0xFF01, 0x3FC0, 0x3E80, 0xFE41, 0xFA01, 0x3AC0,
    0x3B80, 0xFB41, 0x3900, 0xF9C1, 0xF881, 0x3840, 0x2800, 0xE8C1, 0xE981,
    0x2940, 0xEB01, 0x2BC0, 0x2A80, 0xEA41, 0xEE01, 0x2EC0, 0x2F80, 0xEF41,
    0x2D00, 0xEDC1, 0xEC81, 0x2C40, 0xE401, 0x24C0, 0x2580, 0xE541, 0x2700,
    0xE7C1, 0xE681, 0x2640, 0x2200, 0xE2C1, 0xE381, 0x2340, 0xE101, 0x21C0,
    0x2080, 0xE041, 0xA001, 0x60C0, 0x6180, 0xA141, 0x6300, 0xA3C1, 0xA281,
    0x6240, 0x6600, 0xA6C1, 0xA781, 0x6740, 0xA501, 0x65C0, 0x6480, 0xA441,
    0x6C00, 0xACC1, 0xAD81, 0x6D40, 0xAF01, 0x6FC0, 0x6E80, 0xAE41, 0xAA01,
    0x6AC0, 0x6B80, 0xAB41, 0x6900, 0xA9C1, 0xA881, 0x6840, 0x7800, 0xB8C1,
    0xB981, 0x7940, 0xBB01, 0x7BC0, 0x7A80, 0xBA41, 0xBE01, 0x7EC0, 0x7F80,
    0xBF41, 0x7D00, 0xBDC1, 0xBC81, 0x7C40, 0xB401, 0x74C0, 0x7580, 0xB541,
    0x7700, 0xB7C1, 0xB681, 0x7640, 0x7200, 0xB2C1, 0xB381, 0x7340, 0xB101,
    0x71C0, 0x7080, 0xB041, 0x5000, 0x90C1, 0x9181, 0x5140, 0x9301, 0x53C0,
    0x5280, 0x9241, 0x9601, 0x56C0, 0x5780, 0x9741, 0x5500, 0x95C1, 0x9481,
    0x5440, 0x9C01, 0x5CC0, 0x5D80, 0x9D41, 0x5F00, 0x9FC1, 0x9E81, 0x5E40,
    0x5A00, 0x9AC1, 0x9B81, 0x5B40, 0x9901, 0x59C0, 0x5880, 0x9841, 0x8801,
    0x48C0, 0x4980, 0x8941, 0x4B00, 0x8BC1, 0x8A81, 0x4A40, 0x4E00, 0x8EC1,
    0x8F81, 0x4F40, 0x8D01, 0x4DC0, 0x4C80, 0x8C41, 0x4400, 0x84C1, 0x8581,
    0x4540, 0x8701, 0x47C0, 0x4680, 0x8641, 0x8201, 0x42C0, 0x4380, 0x8341,
    0x4100, 0x81C1, 0x8081, 0x4040
)

file_name = 'Settings.json'
RS = None
settings = None

class RS485(UART):
    def __init__(self,
                 id: int = 1,
                 baudrate: int = 9600,
                 data_bits: int = 8,
                 parity=None,
                 stop_bits: int = 1,
                 DE: int = None,
                 collision_check: bool = True):

        if DE is not None:
            self.DE = Pin(DE, Pin.OUT, 0)
        else:
            self.DE = None

        self.collision_check = collision_check

        super().__init__(id, baudrate, data_bits, parity, stop_bits)

        # timing of 1 character in microseconds (us)
        self.t1char = (1000000 * (data_bits + stop_bits + 2)) // baudrate

        # inter-frame delay in microseconds (us)
        # - <= 19200 bps: 3.5x timing of 1 character
        # - > 19200 bps: 1750 us
        if baudrate <= 19200:
            self.inter_frame_delay = (self.t1char * 3500) // 1000
        else:
            self.inter_frame_delay = 1750

    def calc_crc16(self, data: bytearray) -> bytes:
        """
        Calculates the CRC16.

        :param      data:        The data
        :type       data:        bytearray

        :returns:   The crc 16.
        :rtype:     bytes
        """
        crc = 0xFFFF

        for char in data:
            crc = (crc >> 8) ^ CRC16_TABLE[((crc) ^ char) & 0xFF]

        return struct.pack('<H', crc)

    def TX(self, modbus_pdu: bytes, slave_addr: int):
        mb_tx = bytearray()
        mb_tx.append(slave_addr)
        mb_tx.extend(modbus_pdu)
        mb_tx.extend(self.calc_crc16(mb_tx))

        if self.DE is not None:
            self.DE.on()

        self.write(mb_tx)

        while not self.txdone():
            pass

        if self.collision_check:
            echo = self.read()      #discard Echo from the Rx buffer (because RE pin of RS485 transiver is always ON in the board hw)
            if echo != mb_tx:       #verify if TXed packed is sent without collisions
                raise OSError("collision detected: trying to send [TX:{}] but wire out [RX:{}]".format(mb_tx, echo))

        if self.DE is not None:
            self.DE.off()
        return mb_tx

    def RX(self, slave_addr: int, timeout: int):
        discard = False
        mb_rx = bytearray()
        start_time = time.ticks_ms()
        while (time.ticks_ms() - start_time) < timeout:
            rx = self.read(1)
            if rx is not None and len(rx) != 0:
                start_time = time.ticks_us()
                if rx[0] == slave_addr:
                    mb_rx.extend(rx)
                else:
                    raise ValueError('wrong slave address -> {}, should be [{}] ... so drop rest of the frame'.format(rx[0], slave_addr))
                    discard = True
                break
        if discard or len(mb_rx) > 0:
            while (time.ticks_us() - start_time) < self.inter_frame_delay:
                rx = self.read(1)
                if rx is not None and len(rx) != 0:
                    start_time = time.ticks_us()
                    if not discard:
                        mb_rx.extend(rx)
        return mb_rx

WEB = Microdot()

# Function to handle incoming HTTP MB requests
async def handle_request(frm, wr, rs, lg):
    try:
        f = frm[MBAP_HDR_LENGTH-2]+(MBAP_HDR_LENGTH-1)
        if len(frm) > f:
            print('Extra data after MB packet in the TCP buffer [{}] ... ignored'.format(frm[f:].hex()))
        if lg:
            print('   --> [{}]'.format('|'.join('{:02X}'.format(h) for h in frm[:f])))
        rs.read() #discard any intercomunication frames from the Rx buffer (to ensure empty RX buffer)
        t = rs.TX(frm[MBAP_HDR_LENGTH:], frm[MBAP_HDR_LENGTH-1])
        if lg:
            print('   ->- [{}]'.format('|'.join('{:02X}'.format(h) for h in t)))
        r = rs.RX(frm[MBAP_HDR_LENGTH-1], settings["GW"]["time_out"] if settings is not None else 1000)
        l = len(r)
        if l > 0:
            if lg:
                print('   -<- [{}]'.format('|'.join('{:02X}'.format(h) for h in r)))
            RXcrc = r[-CRC_LENGTH:]
            CRC = rs.calc_crc16(r[:-CRC_LENGTH])
            if ((RXcrc[0] is not CRC[0]) or (RXcrc[1] is not CRC[1])):
                raise OSError('invalid response CRC 0x{}, should be [{}]'.format(RXcrc.hex(), CRC.hex()))
            response = bytearray(frm[:MBAP_HDR_LENGTH])
            response[MBAP_HDR_LENGTH-2] = l-CRC_LENGTH
            response.extend(r[1:-CRC_LENGTH])
            if lg:
                print('   <-- [{}]\r\n   ==='.format('|'.join('{:02X}'.format(h) for h in response)))
            wr.write(response)
            await wr.drain()  # Flow control
        else:
            raise OSError('no data received from slave [{}]'.format(frm[MBAP_HDR_LENGTH-1]))
    except Exception as e:
        print("   --- {}:".format(type(e).__name__), e)
        print('   ===')

async def srv(reader, writer):
    while True:
        try:
            frame = await reader.read(300)  # Max number of bytes to read
            if not frame:
                break
            else:
                await handle_request(frame, writer, RS, settings["GW"]["log"] if settings is not None else False)
        except Exception as e:
            print("<MB_recv> [{}]:".format(type(e).__name__), e)
    writer.close()

async def MBgateway(cfg):
    BRD = uname().machine

    if cfg is not None:
        addr=cfg["ETH"]["IP"]
        port=cfg["GW"]["port"]
        tty=cfg["GW"]["tty"]
        TxEN=cfg["GW"]["DE"]
        #log=cfg["GW"]["log"]
    else:
        return

    if tty is None:
        if("VK-RA6M3" in BRD):
            tty=8
        elif("VK-RA6M5" in BRD):
            tty=6
        else:
            print('Specify a UART [Ch] <*.json>')
            return

    if TxEN is None:
        if("VK-RA6M3" in BRD):
            TxEN='P106'
        elif("VK-RA6M5" in BRD):
            TxEN='P507'
        else:
            print('Specify a RS485 [DE] Pin <*.json>')
            return

    global RS
    if cfg is None:
        RS = RS485(id=tty, DE=TxEN)
    else:
        RS = RS485(id=tty, baudrate=cfg["GW"]["baud"], data_bits=cfg["GW"]["data"], parity=cfg["GW"]["parity"], stop_bits= cfg["GW"]["stop"], DE=TxEN)

    try:
        gateway_server = await asyncio.start_server(srv, addr, port, backlog=1)  # self.server = await asyncio.start_server(serve, host, port, ssl=ssl)
    except Exception as e:
        print("<MB_accept> [{}]:".format(type(e).__name__), e) #self.server = await asyncio.start_server(serve, host, port)

    while True:
        try:
            if hasattr(gateway_server, 'serve_forever'):
                try:
                    await gateway_server.serve_forever()
                except asyncio.CancelledError:
                    pass
            await gateway_server.wait_closed()
            break
        except AttributeError:
            # the task hasn't been initialized in the server object yet
            # wait a bit and try again
            await asyncio.sleep(0.1)

@WEB.route('/')   # Main route 
async def hello(request):
    return 'Hello, world {}!'.format(random.randint(0, 9))

async def blink(led, period_ms):
    while True:
        led.on()
        await asyncio.sleep_ms(period_ms)
        led.off()
        await asyncio.sleep_ms(period_ms)

async def main(conf):
    try:
        with open('/flash/' + conf, 'r') as file:
            settings = json.load(file)
    except Exception as e:
        print("<file> [{}]:".format(type(e).__name__), e)

    if settings is not None:
        Eth = network.LAN()
        Eth.config(mac=bytes.fromhex(settings['ETH']['MAC']))
        if settings["ETH"]["DHCP"]:
            print('Taking an IP ...')
        else:
            print('Static IP assignment not supported yet ... trying DHCP')
        Eth.active(True)
        settings["ETH"]["IP"] = Eth.ifconfig()[0]
        print('Got {} from DHCP'.format(Eth.ifconfig()[0]))

        #PIN_task = asyncio.create_task(blink(Pin('LED_R', Pin.OUT),200))
        MB_task = asyncio.create_task(MBgateway(settings))
        WEB_task = asyncio.create_task(WEB.start_server(Eth.ifconfig()[0], port=80))
        await asyncio.gather(MB_task, WEB_task)
    else:
        print('No Settings file found in flash FS')

# Open the file and load the JSON data

asyncio.run(main(file_name))
