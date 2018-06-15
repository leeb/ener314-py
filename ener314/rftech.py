#!/usr/bin/env python3
'''
Receives signals from RFtech temperature sensor
'''

import logging
import time
import rfm69
from registers import *

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s', '%H:%M:%S'))
logger.addHandler(ch)


class RftechPacket(object):
    def __init__(self, addr=None, temp_msb=None, temp_lsb=None):
        self.addr = addr
        self.temp_msb = temp_msb
        self.temp_lsb = temp_lsb

        if isinstance(self.temp_lsb, int) and isinstance(self.temp_msb, int):
            self.temp = 0.0 + self.temp_msb + (self.temp_lsb / 10)
        else:
            self.temp = None

    def __str__(self):
        return "Temperature sensor: {} - {}.{:01d}c".format(self.addr, self.temp_msb, self.temp_lsb)


    @classmethod
    def decode(cls, data):
        #logger.info('raw input {}'.format(data))

        out = []
        dst_mask = 0x01
        length = 0
        state = 1
        trim = 1
        bits = 0

        for v in data:
            src_mask = 0x80
            while src_mask:
                if v & src_mask:
                    if state:
                        length += 1
                    else:
                        # change from low to high
                        if length > 15:
                            break
                        if trim:
                            trim -= 1
                        else:
                            bits += 1
                            dst_mask >>= 1
                            if dst_mask == 0:
                                dst_mask = 0x80
                                out.append(0x0)

                            if length > 7:
                                out[-1] |= dst_mask

                        state = 1
                        length = 1

                else:
                    if state:
                        # change from high to low
                        length = 1
                        state = 0
                    else:
                        length += 1

                src_mask = src_mask >> 1

        if bits != 24:
            return False

        return cls(out[0], out[1], out[2] & 0x0f)



def mode_rftech_receive():
    regset = [
        [ REG_AFCCTRL,          0x20 ],                                  # standard AFC routine
        [ REG_LNA,              RF_LNA_ZIN_50 ],
        [ REG_RXBW,             RF_RXBW_EXP_1 | RF_RXBW_DCCFREQ_010 ],  # 0x41 channel filter bandwidth 120kHz  page:26

        [ REG_OOKPEAK,          0x41 ],
        [ REG_OOKFIX,           0x06 ],

        [ REG_SYNCCONFIG,       RF_SYNC_ON | RF_SYNC_SIZE_2 ],
        [ REG_SYNCVALUE1,       0x80 ],
        [ REG_SYNCVALUE2,       0x00 ],

        [ REG_PACKETCONFIG1,    RF_PACKET1_FORMAT_FIXED | RF_PACKET1_DCFREE_OFF ],
        [ REG_PAYLOADLENGTH,    40 ]
    ]

    rfm69.write_registers(regset)
    rfm69.set_modulation(RF_DATAMODUL_MODULATIONTYPE_OOK)
    rfm69.set_bitrate(RF_BITRATE_2400)
    rfm69.set_preamble(0x0)
    rfm69.set_frequency_deviation(RF_FDEV_5000)
    rfm69.set_frequency(0x6C7AE1)       # 433.92mhz
    rfm69.set_mode_rx()

    rfm69.wait_for(REG_IRQFLAGS1, RF_IRQFLAGS1_MODEREADY, True)
    logger.info('RFM69 Ready')

def listen_test():
    mode_rftech_receive()
    logger.info('In RFTech listen test')

    while 1:
        if rfm69.is_payload_ready():
            pkt = RftechPacket.decode(rfm69.read_fifo())
            if pkt:
                print(pkt)

def main():
    logger.info("Starting up RFTech")
    rfm69.initialize()
    listen_test()
    rfm69.shutdown()


if __name__ == '__main__':
    try:
        main()

    except KeyboardInterrupt:
        rfm69.shutdown()
        pass


