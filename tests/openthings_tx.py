import time
from ener314 import *

if __name__ == '__main__':
    #sensor_id = 0x00072E    # heater
    #sensor_id = 0x00143e    # desk heater
    sensor_id = 0x0017d0

    print("Sending On/Off signal to OpenThings device: 0x{:05X}".format(sensor_id))

    try:
        rfm69.initialize()
        openthings.mode_transmit()

        pkt = openthings.MiHomeSetSwitchState(openthings.PRODUCT_ADAPTER_PLUS, sensor_id, True)

        for n in range(4):
            pkt.switch_state = True if n & 1 else False
            openthings.transmit_payload(pkt.encode())
            time.sleep(2)



    except KeyboardInterrupt:
        pass
    finally:
        print("Shutting down")
        rfm69.shutdown()
