#!/usr/bin/env python

import logging
import RPi.GPIO as GPIO
import spidev
import time
from . registers import *
from . openthings_params import *

GPIO_GRN_LED = 27   # Pin 13
GPIO_RED_LED = 22   # Pin 15

GPIO_SS    = 7   # Pin 26 CE1
GPIO_MOSI  = 10  # Pin 19
GPIO_MISO  = 9   # Pin 21
GPIO_SCK   = 11  # Pin 23
GPIO_RESET = 25  # Pin 22


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s', '%H:%M:%S'))
logger.addHandler(ch)

spi = spidev.SpiDev()


def initialize():
    GPIO.setmode(GPIO.BCM)

    # setup our output pins
    GPIO.setup(GPIO_GRN_LED, GPIO.OUT)
    GPIO.setup(GPIO_RED_LED, GPIO.OUT)
    GPIO.setup(GPIO_RESET, GPIO.OUT)

    spi.open(0, 1)      # select bus 0, CE1
    #spi.max_speed_hz = 9615384
    spi.max_speed_hz = 4807692

    reset_rfm()


def shutdown():
    set_mode_sleep()
    wait_for(REG_IRQFLAGS1, RF_IRQFLAGS1_MODEREADY, True)
    spi.close()
    GPIO.cleanup()


def reg_dump():
    logger.info('PALEVEL:       {:02X}'.format(read_reg(REG_PALEVEL)))

    logger.info('FDEVMSB:       {:02X}'.format(read_reg(REG_FDEVMSB)))
    logger.info('FDEVLSB:       {:02X}'.format(read_reg(REG_FDEVLSB)))

    logger.info('RXBW:          {:02X}'.format(read_reg(REG_RXBW)))

    logger.info('FRFMSB:        {:02X}'.format(read_reg(REG_FRFMSB)))
    logger.info('FRFMID:        {:02X}'.format(read_reg(REG_FRFMID)))
    logger.info('FRFLSB:        {:02X}'.format(read_reg(REG_FRFLSB)))

    logger.info('IRQFLAGS1:     {:02X}'.format(read_reg(REG_IRQFLAGS1)))
    logger.info('IRQFLAGS2:     {:02X}'.format(read_reg(REG_IRQFLAGS2)))

    logger.info('SYNCCONFIG:    {:02X}'.format(read_reg(REG_SYNCCONFIG)))
    logger.info('SYNCVALUE1:    {:02X}'.format(read_reg(REG_SYNCVALUE1)))
    logger.info('SYNCVALUE2:    {:02X}'.format(read_reg(REG_SYNCVALUE2)))

    logger.info('PACKETCONFIG1: {:02X}'.format(read_reg(REG_PACKETCONFIG1)))



def blink():
    green_led(True)
    time.sleep(.2)
    red_led(True)
    time.sleep(.2)
    green_led(False)
    time.sleep(.2)
    red_led(False)
    time.sleep(.2)


def reset_rfm():
    ''' Hard reset the RFM module '''

    GPIO.output(GPIO_RESET, GPIO.HIGH);
    green_led(True)
    red_led(True)
    time.sleep(0.1)

    GPIO.output(GPIO_RESET, GPIO.LOW);
    green_led(False)
    red_led(False)
    time.sleep(0.1)


def set_modulation(data):
    write_reg(REG_DATAMODUL, data)

def set_preamble(size):
    write_reg(REG_PREAMBLEMSB, size >> 8 & 0xff)
    write_reg(REG_PREAMBLELSB, size & 0xff)

def set_bitrate(bps):
    write_reg(REG_BITRATEMSB, bps >> 8 & 0xff)
    write_reg(REG_BITRATELSB, bps & 0xff)

def set_frequency_deviation(freq):
    write_reg(REG_FDEVMSB, freq >> 8 & 0xff)
    write_reg(REG_FDEVLSB, freq & 0xff)

def set_frequency(freq):
    write_reg(REG_FRFMSB, freq >> 16 & 0xff)
    write_reg(REG_FRFMID, freq >> 8 & 0xff)
    write_reg(REG_FRFLSB, freq & 0xff)

def set_power(pwr):
    write_reg(REG_PALEVEL, pwr)

def set_mode(mode):
    write_reg(REG_OPMODE, mode)

def set_mode_tx():
    set_mode(RF_OPMODE_TRANSMITTER)

def set_mode_rx():
    set_mode(RF_OPMODE_RECEIVER)

def set_mode_sleep():
    set_mode(RF_OPMODE_SLEEP)

def read_reg(addr):
    return spi.xfer([addr & 0x7F, 0])[1]

def write_reg(addr, value):
    spi.xfer([addr | 0x80, value])

def write_registers(regset):
    for reg in regset:
        write_reg(reg[0], reg[1])

def write_fifo(data):
    spi.xfer([REG_FIFO | 0x80] + data)

def read_fifo():
    buf = []
    while read_reg(REG_IRQFLAGS2) & RF_IRQFLAGS2_FIFONOTEMPTY:
        buf.append(read_reg(REG_FIFO))
    return buf

def is_payload_ready():
    if read_reg(REG_IRQFLAGS2) & RF_IRQFLAGS2_PAYLOADREADY:
        return True
    return False



def wait_for(addr, mask, val, timeout=1):
    while 1:
        r = read_reg(addr)
        if ((r & mask) == (mask if val else 0)):
            return True

        if timeout < 0:
            logger.error('wait for timeout Reg: {:02X} Expected: {:08b} Got: {:08b}'.format(addr, mask, r))
            return False

        time.sleep(0.01)
        timeout = timeout - 0.01


def green_led(state):
    if state:
        GPIO.output(GPIO_GRN_LED, GPIO.HIGH)
    else:
        GPIO.output(GPIO_GRN_LED, GPIO.LOW)

def red_led(state):
    if state:
        GPIO.output(GPIO_RED_LED, GPIO.HIGH)
    else:
        GPIO.output(GPIO_RED_LED, GPIO.LOW)



def main():
    logger.info("Starting up")
    initialize()
    shutdown()


if __name__ == '__main__':
    try:
        main()

    except KeyboardInterrupt:
        shutdown()
        pass