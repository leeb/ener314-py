#!/usr/bin/env python

import RPi.GPIO as GPIO
from time import sleep


LED_GRN = 27
LED_RED = 22


GPIO.setmode(GPIO.BCM)

# setup our output pins
GPIO.setup(LED_GRN, GPIO.OUT)
GPIO.setup(LED_RED, GPIO.OUT)


while True:
	GPIO.output(LED_RED, GPIO.HIGH)
	GPIO.output(LED_GRN, GPIO.HIGH)
	sleep(1)

	GPIO.output(LED_RED, GPIO.LOW)
	GPIO.output(LED_GRN, GPIO.HIGH)
	sleep(1)

	GPIO.output(LED_RED, GPIO.HIGH)
	GPIO.output(LED_GRN, GPIO.LOW)
	sleep(1)

	GPIO.output(LED_RED, GPIO.LOW)
	GPIO.output(LED_GRN, GPIO.LOW)
	sleep(1)
