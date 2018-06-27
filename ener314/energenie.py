#!/usr/bin/env python3
'''
Implements the legacy OOK modulation Energnie protocol.
'''

import logging
import time
from . import rfm69
from .registers import *

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s', '%H:%M:%S'))
logger.addHandler(ch)

REPEATS = 12


class EnergeniePacket(object):
    def __init__(self, addr=0, state=0):
        self.addr = addr
        self.state = state

    def __str__(self):
        return "Address: {:05X} State: {:01X}".format(self.addr, self.state)

    @classmethod
    def decode(cls, data):
        if len(data) != 12:
            return False

        dat = 0
        for v in data:
            dat = dat << 2
            if v == 0x44:
                dat |= 3;
            elif v == 0x47:
                dat |= 2
            elif v == 0x74:
                dat |= 1
            elif v != 0x77:
                return False

        return cls(dat >> 4, dat & 0xf)

    def encode(self):
        value = (self.addr << 4) | (self.state & 0xf)
        data = []

        for i in range(0, 12):
            value = value << 2
            if (value & 0x3000000) == 0x0000000:
                data.append(0x77)
                #data.append(0xEE)
            if (value & 0x3000000) == 0x1000000:
                data.append(0x74)
                #data.append(0xE8)
            if (value & 0x3000000) == 0x2000000:
                data.append(0x47)
                #data.append(0x8E)
            if (value & 0x3000000) == 0x3000000:
                data.append(0x44)
                #data.append(0x88)

        return [0x80, 0, 0, 0] + data





def mode_energenie_transmit():
    regset = [
        [ REG_RXBW,             RF_RXBW_EXP_1 | RF_RXBW_DCCFREQ_010 ],  # 0x41 channel filter bandwidth 120kHz  page:26
        [ REG_SYNCCONFIG,       RF_SYNC_OFF ],
        [ REG_PACKETCONFIG1,    RF_PACKET1_FORMAT_FIXED | RF_PACKET1_DCFREE_OFF ],
        [ REG_PAYLOADLENGTH,    48 ],       # fixed length, 12 bytes
        [ REG_FIFOTHRESH,       16 ]        # 4 byte sync + 10 bytes address +
    ]

    logger.info('RFM69 Mode:Energenie TX')

    rfm69.write_registers(regset)
    rfm69.set_modulation(RF_DATAMODUL_MODULATIONTYPE_OOK)
    rfm69.set_power(RF_PALEVEL_PA0_ON | RF_PALEVEL_OUTPUTPOWER_11111)
    rfm69.set_bitrate(RF_BITRATE_4800)
    rfm69.set_preamble(0)
    rfm69.set_frequency_deviation(RF_FDEV_5000)
    rfm69.set_frequency(0x6C7AE1)       # 433.92mhz
    rfm69.set_mode_tx()

    rfm69.wait_for(REG_IRQFLAGS1, RF_IRQFLAGS1_MODEREADY, True)
    logger.info('RFM69 Ready')


def mode_energenie_receive():
    regset = [
        [ REG_AFCCTRL,          0x0 ],                                  # standard AFC routine
        [ REG_LNA,              RF_LNA_ZIN_50 ],
        [ REG_RXBW,             RF_RXBW_EXP_1 | RF_RXBW_DCCFREQ_010 ],  # 0x41 channel filter bandwidth 120kHz  page:26

        [ REG_OOKPEAK,          0x41 ],
        [ REG_OOKFIX,           0x06 ],

        [ REG_SYNCCONFIG,       RF_SYNC_ON | RF_SYNC_SIZE_4 ],
        [ REG_SYNCVALUE1,       0x80 ],
        [ REG_SYNCVALUE2,       0x00 ],
        [ REG_SYNCVALUE3,       0x00 ],
        [ REG_SYNCVALUE4,       0x00 ],

        [ REG_PACKETCONFIG1,    RF_PACKET1_FORMAT_FIXED | RF_PACKET1_DCFREE_OFF ],
        [ REG_PAYLOADLENGTH,    12 ]             # fixed length, 12 bytes
    ]

    rfm69.write_registers(regset)
    rfm69.set_modulation(RF_DATAMODUL_MODULATIONTYPE_OOK)
    rfm69.set_bitrate(RF_BITRATE_4800)
    rfm69.set_preamble(0)
    rfm69.set_frequency_deviation(RF_FDEV_5000)
    rfm69.set_frequency(0x6C7AE1)       # 433.92mhz
    rfm69.set_mode_rx()

    rfm69.wait_for(REG_IRQFLAGS1, RF_IRQFLAGS1_MODEREADY, True)
    logger.info('RFM69 Ready')


def transmit_payload(data, repeats=REPEATS):
    if rfm69.wait_for(REG_IRQFLAGS1, RF_IRQFLAGS1_MODEREADY | RF_IRQFLAGS1_TXREADY, True):

        # print('buffer {}'.format(data))
        # print('flags   {:08b} {:08b}'.format(rfm69.read_reg(REG_IRQFLAGS2), rfm69.read_reg(REG_IRQFLAGS1)))

        for r in range(repeats):
            rfm69.wait_for(REG_IRQFLAGS2, RF_IRQFLAGS2_FIFOLEVEL, False);
            rfm69.write_fifo(data)

        # wait for Packet sent
        rfm69.wait_for(REG_IRQFLAGS2, RF_IRQFLAGS2_PACKETSENT, True);


