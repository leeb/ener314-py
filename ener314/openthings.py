#!/usr/bin/env python3
'''
Implements the OpenThings FSK modulation used by Energenie MiHome devices
'''

import logging
import time
import random
from . import rfm69
from .registers import *
from .openthings_params import *

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s', '%H:%M:%S'))
logger.addHandler(ch)

RF_AFCCTRL_STANDARD = 0

MANUFACTURER_MIHOME  = 0x04

PRODUCT_MONITOR      = 0x01
PRODUCT_ADAPTER_PLUS = 0x02


class OpenThingsPacket(object):
    def __init__(self, seed=None, crc=None, **kwargs):

        self.join = True if kwargs.get('join', False) else False
        self.sensor_id = kwargs.get('sensor_id', None)
        self.seed = seed
        self.crc = crc

    def __str__(self):
        # r = "Size: {}\n".format(self.size)
        r = "Manufacturer ID: {}\n".format(self.manufacturer_id) + \
            "Product ID: {}\n".format(self.product_id) + \
            "Seed: {:04X}\n".format(self.seed) + \
            "Sensor: {:06X}\n".format(self.sensor_id) + \
            "Join: {}\n".format(self.join)
        return r

    def encode(self, payload):
        seed = random.randint(0, 65535)

        data = []

        # build 8 byte header
        data.append(OPENTHINGS_HEADER_SIZE - 1)

        data.append(self.manufacturer_id)
        data.append(self.product_id)

        data.append(seed >> 8 & 0xff)
        data.append(seed & 0xff)

        data.append(self.sensor_id >> 16 & 0xff)
        data.append(self.sensor_id >> 8 & 0xff)
        data.append(self.sensor_id & 0xff)

        # add the payload
        data = data + payload

        # calcualte crc
        data.append(0)
        crc = self.crc(data, len(data))
        data.append(crc >> 8 & 0xff)
        data.append(crc & 0xff)

        # adjust length
        data[0] = len(data) - 1

        logger.info("payload data {}".format(data))

        # encrypt data
        self.crypt(data, seed)
        logger.info("encrypt data {}".format(data))

        return data


    @classmethod
    def crc(cls, data, size):
        val = 0

        for i in range(5, size):
            val = val ^ (data[i] << 8)

            for r in range(8, 0, -1):
                val = ((val << 1) ^ 0x1021) if (val & (1 << 15)) else  (val << 1);
                val &= 0xffff
                # logger.info('crc calc {} {} {:02X}'.format(i, r, val))

        return val

    @classmethod
    def crypt(cls, data, seed):
        seed = (242 << 8) ^ seed;
        #logger.info('encrypt = {:02X} {:02X} {:02X}'.format(data[5], data[6], data[7]))

        for i in range(5, len(data)):
            for r in range(5):
                seed = ((seed >> 1) ^ 62965) if (seed & 1) else (seed >> 1)
            data[i] = (seed ^ data[i] ^ 90) & 0xff



    def set_switch_state(self, state):
        data = [
            0x80 | OPENTHINGS_SWITCH_STATE,
            1,
            0 if state else 1
        ]
        return data



class MiHomeMonitorPacket(OpenThingsPacket):
    def __init__(self, **kwargs):
        self.manufacturer_id = MANUFACTURER_MIHOME
        self.product_id = PRODUCT_MONITOR
        super(MiHomeMonitorPacket, self).__init__(**kwargs)

        self.real_power = kwargs.get('real_power', 0)
        self.reactive_power = kwargs.get('reactive_power', 0)
        self.voltage = kwargs.get('voltage', 230)
        self.frequency = kwargs.get('frequency', 50.0)

    def __str__(self):
        r = "MiHome Power Monitor\n" + super(MiHomeMonitorPacket, self).__str__()
        r = r + "Voltage: {:d}\n".format(self.voltage)
        r = r + "Real power: {:d}\n".format(self.real_power)
        r = r + "Reactive power: {:d}\n".format(self.reactive_power)
        r = r + "Frequency: {}\n".format(self.frequency)
        return r



class MiHomeAdapterPlusPacket(OpenThingsPacket):
    def __init__(self, **kwargs):
        self.manufacturer_id = MANUFACTURER_MIHOME
        self.product_id = PRODUCT_ADAPTER_PLUS
        super(MiHomeAdapterPlusPacket, self).__init__(**kwargs)

        self.state = kwargs.get('state', None)
        self.real_power = kwargs.get('real_power', 0)
        self.reactive_power = kwargs.get('reactive_power', 0)
        self.voltage = kwargs.get('voltage', 230)
        self.frequency = kwargs.get('frequency', 50)

    def __str__(self):
        r = "MiHome Adapter Plus\n" + super(MiHomeAdapterPlusPacket, self).__str__()
        r = r + "Switch state: {}\n".format('On' if self.state else 'Off')
        r = r + "Voltage: {:d}\n".format(self.voltage)
        r = r + "Real power: {:d}\n".format(self.real_power)
        r = r + "Reactive power: {:d}\n".format(self.reactive_power)
        r = r + "Frequency: {}\n".format(self.frequency)
        return r




def mode_openthings_transmit():
    regset = [
        #[ REG_AFCFEI,           RF_AFCFEI_AFCAUTO_ON ],                # AFC is performed each time rx mode is entered
        #[ REG_RSSITHRESH,       0xDC ],                                # RSSI threshold 0xE4 -> 0xDC (220)

        [ REG_SYNCCONFIG,       RF_SYNC_ON | RF_SYNC_SIZE_2 ],      # Size of the Synch word = 2 (SyncSize + 1)
        [ REG_SYNCVALUE1,       0x2D ],                             # 1st byte of Sync word
        [ REG_SYNCVALUE2,       0xD4 ],                             # 2nd byte of Sync word

        # Variable length, Manchester coding, Addr must match NodeAddress
        [ REG_PACKETCONFIG1,    RF_PACKET1_FORMAT_VARIABLE | RF_PACKET1_DCFREE_MANCHESTER ],
        [ REG_FIFOTHRESH,       RF_FIFOTHRESH_TXSTART_FIFONOTEMPTY ]        # Condition to start packet transmission: at least one byte in FIFO
    ]

    rfm69.write_registers(regset)
    rfm69.set_modulation(RF_DATAMODUL_MODULATIONTYPE_FSK)
    rfm69.set_power(RF_PALEVEL_PA0_ON | RF_PALEVEL_OUTPUTPOWER_11111)
    rfm69.set_bitrate(RF_BITRATE_4800)
    rfm69.set_preamble(3)
    rfm69.set_frequency_deviation(RF_FDEV_5000)
    rfm69.set_frequency(0x6C9333)       # 434.3mhz
    rfm69.set_mode_tx()

    rfm69.wait_for(REG_IRQFLAGS1, RF_IRQFLAGS1_MODEREADY, True)
    logger.info('RFM69 Ready')


def mode_openthings_receive():
    regset = [
        [ REG_AFCCTRL,          RF_AFCCTRL_STANDARD ],                  # standard AFC routine
        [ REG_LNA,              RF_LNA_ZIN_50 ],                        # 200ohms, gain by AGC loop -> 50ohms
        [ REG_RXBW,             RF_RXBW_EXP_3 | RF_RXBW_DCCFREQ_010 ],  # 0x43 channel filter bandwidth 10kHz -> 60kHz  page:26

        #[ REG_AFCFEI,           RF_AFCFEI_AFCAUTO_ON ],                # AFC is performed each time rx mode is entered
        #[ REG_RSSITHRESH,       0xDC ],                                # RSSI threshold 0xE4 -> 0xDC (220)

        [ REG_SYNCCONFIG,       RF_SYNC_ON | RF_SYNC_SIZE_2 ],      # Size of the Synch word = 2 (SyncSize + 1)
        [ REG_SYNCVALUE1,       0x2D ],                             # 1st byte of Sync word
        [ REG_SYNCVALUE2,       0xD4 ],                             # 2nd byte of Sync word

        # Variable length, Manchester coding, Addr must match NodeAddress
        [ REG_PACKETCONFIG1,    RF_PACKET1_FORMAT_VARIABLE | RF_PACKET1_DCFREE_MANCHESTER ],
        [ REG_PAYLOADLENGTH,    RF_PAYLOADLENGTH_VALUE ],             # max Length in RX, not used in Tx
    ]

    rfm69.write_registers(regset)
    rfm69.set_modulation(RF_DATAMODUL_MODULATIONTYPE_FSK)
    rfm69.set_bitrate(RF_BITRATE_4800)
    rfm69.set_preamble(3)
    rfm69.set_frequency_deviation(RF_FDEV_5000)
    rfm69.set_frequency(0x6C9333)       # 434.3mhz
    rfm69.set_mode_rx()

    rfm69.wait_for(REG_IRQFLAGS1, RF_IRQFLAGS1_MODEREADY, True)
    logger.info('RFM69 Ready')




def decode_payload(data):
    if len(data) < OPENTHINGS_HEADER_SIZE:
        return None

    pkt_size = data[0] + 1
    manufacturer_id = data[1]
    product_id = data[2]
    seed = data[3] << 8 | data[4]

    logger.info("== Packet Bytes:{} manufacturer:{} product:{}".format(pkt_size, manufacturer_id, product_id))

    # length check
    if len(data) != pkt_size:
        return None

    OpenThingsPacket.crypt(data, seed)
    crc = (data[pkt_size - 2] << 8) | data[pkt_size - 1]

    if OpenThingsPacket.crc(data, pkt_size - 2) != crc:
        logger.warning('Bad crc {} {:04X}'.format(pkt_size, crc))
        return None

    kwargs = {
        'size': pkt_size,
        'sensor_id': data[5] << 16 | data[6] << 8 | data[7]
    }

    i = 8
    while i < pkt_size:
        param = data[i]

        if param == 0:  # crc already
            break

        d_type = data[i + 1] >> 4
        d_size = data[i + 1] & 0x0f
        i += 2

        if param == OPENTHINGS_REAL_POWER:
            if d_type == 8 and d_size == 2:
                kwargs['real_power'] = (data[i] << 8) + data[i + 1]

        elif param == OPENTHINGS_REACTIVE_POWER:
            if d_type == 8 and d_size == 2:
                kwargs['reactive_power'] = (data[i] << 8) + data[i + 1]

        elif param == OPENTHINGS_VOLTAGE:
            if d_type == 0 and d_size == 1:
                kwargs['voltage'] = data[i]

        elif param == OPENTHINGS_FREQUENCY:
            if d_type == 2 and d_size == 2:
                kwargs['frequency'] = float(data[i]) + (float(data[i + 1]) / 256)

        elif param == OPENTHINGS_SWITCH_STATE:
            kwargs['state'] = data[i]

        elif param == OPENTHINGS_JOIN:
            self.join = True

        i += d_size

    if manufacturer_id == MANUFACTURER_MIHOME:
        if product_id == PRODUCT_MONITOR:
            return MiHomeMonitorPacket(seed=seed, crc=crc, **kwargs)
        elif product_id == PRODUCT_ADAPTER_PLUS:
            return MiHomeAdapterPlusPacket(seed=seed, crc=crc, **kwargs)
        else:
            return None

    return None


def receive_payload():
    return decode_payload(rfm69.read_fifo())


def transmit_payload(data):
    if rfm69.wait_for(REG_IRQFLAGS1, RF_IRQFLAGS1_MODEREADY | RF_IRQFLAGS1_TXREADY, True):
        if rfm69.wait_for(REG_IRQFLAGS2, RF_IRQFLAGS2_FIFONOTEMPTY, False):
            rfm69.write_fifo(data)

            # wait for packet send?

