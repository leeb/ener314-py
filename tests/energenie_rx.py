from ener314 import *

if __name__ == '__main__':
    try:
        rfm69.initialize()
        energenie.mode_receive()
        print("Listening for legacy Energenie OOK modulated packets")

        while True:
            if rfm69.is_payload_ready():
                pkt = energenie.receive_payload()
                if pkt:
                    print(pkt)

    except KeyboardInterrupt:
        pass
    finally:
        print("Shutting down")
        rfm69.shutdown()
