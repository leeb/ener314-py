import time
from ener314 import *

if __name__ == '__main__':
    device_id = 0x0632

    print("Sending On/Off signal to Tesco device: 0x{:05X}".format(device_id))

    try:
        rfm69.initialize()
        tesco.mode_tesco_transmit()

        pkt = TescoPacket(device_id, 0x51)
        tesco.transmit_payload(pkt.encode())
        time.sleep(2)

        pkt = TescoPacket(device_id, 0x50)
        tesco.transmit_payload(pkt.encode())
        time.sleep(2)

    except KeyboardInterrupt:
        pass
    finally:
        print("Shutting down")
        rfm69.shutdown()
