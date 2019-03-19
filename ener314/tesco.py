#!/usr/bin/env python3
'''
Implements OOK protocol from mystery tesco adapter
based on EM78P153S controller
Model number: REMSOC2-TD

Devices have a 16 bit address
Bits 4-7 of state address adapters
0x10 to 0x40 refer to individual adapters
0x50 controls entire group.

Bit 0 controls power
0x00 Off
0x01 On

High nibble of state addresses the individual
'''

import logging
import time
import random
from . import rfm69
from .registers import *

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s', '%H:%M:%S'))
logger.addHandler(ch)

REPEATS = 12


class TescoPacket(object):
    def __init__(self, addr=0, state=0):
        self.addr = addr
        self.state = state

    def __str__(self):
        return "Address: {:04X} State: {:01X}".format(self.addr, self.state)

    def encode(self):
        data = [
            (self.addr >> 8) & 0xff,
            self.addr & 0xff,
            random.randint(0, 255),
            self.state & 0xff,
            0
        ]
        data[4] = (data[0] + data[1] + data[2] + data[3]) & 0xff
        logger.info('Data: {}'.format(data))

        # sync pattern (8 bytes)
        #out = [ 0xC0, 0, 0, 0, 0, 0, 0xFF, 0xFF ]
        out = []
        for i in range(6):  # 24 pips (18 bytes)
            out += [ 0x0C, 0x30, 0xC3 ]

        # final short pip, 00011xxx, making 27 bytes
        out.append(0x18)

        dst_mask = 0x04
        for v in data:
            src_mask = 0x80
            while src_mask:

                zero_bits = 3
                if src_mask & v:
                    zero_bits = 4

                for r in range(zero_bits):
                    dst_mask = dst_mask >> 1
                    if dst_mask == 0:
                        dst_mask = 0x80
                        out.append(0x0)

                for r in range(2):
                    out[-1] = out[-1] | dst_mask
                    dst_mask = dst_mask >> 1
                    if dst_mask == 0:
                        dst_mask = 0x80
                        out.append(0x0)

                src_mask = src_mask >> 1

        return out


def mode_transmit():
    rfm69.set_mode_standby()

    rfm69.set_modulation(RF_DATAMODUL_MODULATIONTYPE_OOK)
    rfm69.set_frequency_deviation(RF_FDEV_5000)
    rfm69.set_frequency(0x6C7AE1)       # 433.92mhz
    rfm69.set_power(RF_PALEVEL_PA0_ON | RF_PALEVEL_OUTPUTPOWER_11111)

    rfm69.set_bitrate(RF_BITRATE_4800)
    rfm69.set_preamble(3)
    rfm69.set_sync(RF_SYNC_ON | RF_SYNC_SIZE_8, [0xC0,0x00,0x00,0x00,0x00,0x00,0xFF,0xFF])

    rfm69.set_packet_config(RF_PACKET1_FORMAT_FIXED)
    rfm69.set_payload_length(64)
    rfm69.set_fifo_threshold(RF_FIFOTHRESH_TXSTART_FIFONOTEMPTY)
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
    rfm69.set_sync(RF_SYNC_ON | RF_SYNC_SIZE_8, [0xc0,0x00,0x00,0x00,0x00,0x00,0xff,0xff])

    rfm69.set_packet_config(RF_PACKET1_FORMAT_FIXED | RF_PACKET1_DCFREE_OFF)
    rfm69.set_payload_length(50)
    rfm69.set_automode(RF_AUTOMODES_ENTER_OFF | RF_AUTOMODES_EXIT_OFF)

    rfm69.wait_for(REG_IRQFLAGS1, RF_IRQFLAGS1_MODEREADY, True)
    logger.info('RFM69 Ready')


def decode_payload(data):
    # logger.info('raw input {}'.format(data))
    out = []
    dst_mask = 0x01
    length = 0
    state = 1
    trim = 25
    bits = 0

    for v in data:
        src_mask = 0x80
        while src_mask and bits < 40:
            if v & src_mask:
                if state:
                    length +=1
                else:
                    if trim:
                        trim -= 1
                    else:
                        bits += 1
                        dst_mask >>= 1
                        if dst_mask == 0:
                            dst_mask = 0x80
                            out.append(0x0)
                        if length > 3:
                            out[-1] |= dst_mask
                    state = 1
                    length = 1

            else:
                if state:
                    length = 1
                    state = 0
                else:
                    length += 1
            src_mask >>= 1

    # trivial validation
    if bits != 40:
        return None

    crc = 0xff & (out[0] + out[1] + out[2] + out[3])
    if out[4] != crc:
        return None

    #logger.info('Bits {} result {}'.format(bits, out))
    addr = (out[0] << 8) + out[1]

    return TescoPacket(addr, out[3])


def receive_payload():
    return decode_payload(rfm69.read_fifo())


def transmit_payload(data, repeats=REPEATS):
    if rfm69.wait_for(REG_IRQFLAGS2, RF_IRQFLAGS2_FIFONOTEMPTY, False):
        rfm69.write_fifo(data)
        rfm69.wait_for(REG_IRQFLAGS1, RF_IRQFLAGS1_AUTOMODE, False)

