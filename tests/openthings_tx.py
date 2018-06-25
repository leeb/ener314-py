import time
from ener314 import *

if __name__ == '__main__':
    sensor_id = 0x00072E

    print("Sending On/Off signal to OpenThings device: 0x{:05X}".format(sensor_id))

    try:
        rfm69.initialize()
        openthings.mode_openthings_transmit()

        pkt = OpenThingsPacket()
        pkt.manufacturer_id = 4
        pkt.product_id = 2
        pkt.sensor_id = sensor_id

        # For switch state, 0 = on, 1 = off
        openthings.transmit_payload(pkt.encode(pkt.set_switch_state(0)))
        time.sleep(2)

        openthings.transmit_payload(pkt.encode(pkt.set_switch_state(1)))
        time.sleep(2)


    except KeyboardInterrupt:
        pass
    finally:
        print("Shutting down")
        rfm69.shutdown()
