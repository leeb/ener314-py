# Receive and display temperature data from RF Tech sensor

import time
from ener314 import *

if __name__ == '__main__':
    try:
        rfm69.initialize()
        rftech.mode_receive()
        print("Listening for temperature packets")

        while True:
            if rfm69.is_payload_ready():
                pkt = rftech.receive_payload()
                if pkt:
                    print(pkt)
            else:
                time.sleep(0.1)

    except KeyboardInterrupt:
        pass
    finally:
        print("Shutting down")
        rfm69.shutdown()

