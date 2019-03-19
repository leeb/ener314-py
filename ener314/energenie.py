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

REPEATS = 15


class EnergeniePacket(object):
    def __init__(self, addr=0, state=0):
        self.addr = addr
        self.state = state

    def __str__(self):
        return "Address: {:05X} State: {:01X}".format(self.addr, self.state)

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

        return data


def mode_transmit():
    rfm69.set_mode_standby()

    rfm69.set_modulation(RF_DATAMODUL_MODULATIONTYPE_OOK)
    rfm69.set_frequency_deviation(RF_FDEV_5000)
    rfm69.set_frequency(0x6C7AE1)       # 433.92mhz
    rfm69.set_power(RF_PALEVEL_PA0_ON | RF_PALEVEL_OUTPUTPOWER_11111)

    rfm69.set_bitrate(RF_BITRATE_4800)
    rfm69.set_preamble(0)
    rfm69.set_sync(RF_SYNC_OFF)
    #rfm69.set_sync(RF_SYNC_ON | RF_SYNC_SIZE_4, [0x80,0x00,0x00,0x00])

    rfm69.set_packet_config(RF_PACKET1_FORMAT_FIXED)
    #rfm69.set_packet_config(RF_PACKET1_FORMAT_VARIABLE)
    rfm69.set_payload_length(64)
    rfm69.set_fifo_threshold(RF_FIFOTHRESH_TXSTART_FIFONOTEMPTY | 15)
    rfm69.set_automode(RF_AUTOMODES_ENTER_FIFONOTEMPTY | RF_AUTOMODES_EXIT_PACKETSENT | RF_AUTOMODES_INTERMEDIATE_TRANSMITTER)

    rfm69.wait_for(REG_IRQFLAGS1, RF_IRQFLAGS1_MODEREADY, True)
    logger.info('RFM69 Ready')


def mode_receive():
    rfm69.set_mode_rx()

    rfm69.set_modulation(RF_DATAMODUL_MODULATIONTYPE_OOK)
    rfm69.set_frequency_deviation(RF_FDEV_5000)
    rfm69.set_frequency(0x6C7AE1)       # 433.92mhz

    rfm69.write_reg(REG_AFCCTRL, 0x00)
    rfm69.write_reg(REG_LNA, RF_LNA_ZIN_50)
    rfm69.write_reg(REG_RXBW, RF_RXBW_EXP_1 | RF_RXBW_DCCFREQ_010)
    rfm69.write_reg(REG_OOKPEAK, 0x41)
    rfm69.write_reg(REG_OOKFIX, 0x06)

    rfm69.set_bitrate(RF_BITRATE_4800)
    rfm69.set_preamble(0)
    rfm69.set_sync(RF_SYNC_ON | RF_SYNC_SIZE_4, [0x80,0x00,0x00,0x00])

    rfm69.set_packet_config(RF_PACKET1_FORMAT_FIXED | RF_PACKET1_DCFREE_OFF)
    rfm69.set_payload_length(12)
    rfm69.set_automode(RF_AUTOMODES_ENTER_OFF | RF_AUTOMODES_EXIT_OFF)

    rfm69.wait_for(REG_IRQFLAGS1, RF_IRQFLAGS1_MODEREADY, True)
    logger.info('RFM69 Ready')


def decode_payload(data):
    if len(data) != 12:
        return None

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
            return None

    return EnergeniePacket(dat >> 4, dat & 0xf)


def receive_payload():
    return decode_payload(rfm69.read_fifo())


def transmit_payload(data, repeats=REPEATS):
    data = [0x80, 0, 0, 0] + data

    #logger.info("Sending {} times: {}".format(repeats, data))
    rfm69.wait_for(REG_IRQFLAGS2, RF_IRQFLAGS2_FIFONOTEMPTY, False)
    rfm69.write_fifo([0 for n in range(16)])
    if rfm69.wait_for(REG_IRQFLAGS1, RF_IRQFLAGS1_AUTOMODE | RF_IRQFLAGS1_TXREADY, True):
        for r in range(repeats):
            rfm69.wait_for(REG_IRQFLAGS2, RF_IRQFLAGS2_FIFOLEVEL, False);
            rfm69.write_fifo(data)

    # wait for automode to deactivate transmitter, returning to standby
    rfm69.wait_for(REG_IRQFLAGS1, RF_IRQFLAGS1_AUTOMODE, False)

    #rfm69.wait_for(REG_IRQFLAGS2, RF_IRQFLAGS2_FIFONOTEMPTY, False)
        # print('buffer {}'.format(data))
        # print('flags   {:08b} {:08b}'.format(rfm69.read_reg(REG_IRQFLAGS2), rfm69.read_reg(REG_IRQFLAGS1)))
    #        if rfm69.wait_for(REG_IRQFLAGS2, RF_IRQFLAGS2_FIFONOTEMPTY, False):
                #rfm69.wait_for(REG_IRQFLAGS2, RF_IRQFLAGS2_FIFOLEVEL, False);

