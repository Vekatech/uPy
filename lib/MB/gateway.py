import time
import struct
import socket
import network
from os import uname
from machine import Pin, UART

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

# Function to handle incoming HTTP MB requests
def handle_request(frm, rs, clnt, lg):
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
        r = rs.RX(frm[MBAP_HDR_LENGTH-1], 1000)
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
            clnt.send(response)
        else:
            raise OSError('no data received from slave [{}]'.format(frm[MBAP_HDR_LENGTH-1]))
    except Exception as e:
        print("   --- {}:".format(type(e).__name__), e)
        print('   ===')

def ON(log=False, tty=None, TxEN=None):
    BRD = uname().machine

    if tty is None:
        if("VK-RA6M3" in BRD):
            tty=8 #RS = RS485(id=8, DE='P106')
        elif("VK-RA6M5" in BRD):
            tty=6 #RS = RS485(id=6, DE='P507')
        else:
            print('Specify a UART [Ch] <module>.ON(tty=Ch)')
            return

    if TxEN is None:
        if("VK-RA6M3" in BRD):
            TxEN='P106' #RS = RS485(id=8, DE='P106')
        elif("VK-RA6M5" in BRD):
            TxEN='P507' #RS = RS485(id=6, DE='P507')
        else:
            print('Specify a RS485 [DE] Pin <module>.ON(TxEN=DE)')
            return
    
    RS = RS485(id=tty, DE=TxEN)

    Lan = network.LAN()
    print('Taking an IP ...')
    Lan.active(True)
    
    addr = (Lan.ifconfig()[0], 502)

    # Create a server socket
    server = socket.socket()
    server.bind(addr)
    server.listen(1)
    print('Listening on {}:{}'.format(addr[0], addr[1]))

    while True:
        try:
            print('Waiting Clients ...')
            client, addr_info = server.accept()
            print("-> {}:{}".format(addr_info[0],addr_info[1]))
            while True:
                try:
                    frame = client.recv(300)
                except Exception as e:
                    print("Error [recv]:", e)
                if len(frame) == 0:
                    client.close()
                    break
                else:
                    handle_request(frame, RS, client, log)
        except Exception as e:
            print("Error [accept]:", e)
