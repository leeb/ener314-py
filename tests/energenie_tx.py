import time
from ener314 import *

if __name__ == '__main__':
    # device_id = 0x05b421    # 4 gang extension
    # device_id = 0x08a39c    # desk lamp
    device_id = 0x07b2df    # spot light
    # device_id = 0x00372f    # window light
    # device_id = 0x047d8f    # unit light

    print("Sending On/Off signal to legacy Energnie device: 0x{:05X}".format(device_id))

    try:
        rfm69.initialize()
        energenie.mode_transmit()

        for i in range(2):
            print("on")
            pkt = energenie.EnergeniePacket(device_id, 0x0)
            energenie.transmit_payload(pkt.encode())
            time.sleep(2)

            print("off")
            pkt = energenie.EnergeniePacket(device_id, 0x1)
            energenie.transmit_payload(pkt.encode())
            time.sleep(2)



    except KeyboardInterrupt:
        pass
    finally:
        print("Shutting down")
        rfm69.shutdown()
