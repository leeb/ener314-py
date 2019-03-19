from ener314 import *

if __name__ == '__main__':
    try:
        rfm69.initialize()
        tesco.mode_receive()
        print("Listening for Tesco OOK modulated packets")

        while True:
            if rfm69.is_payload_ready():
                pkt = tesco.receive_payload()
                if pkt:
                    print(pkt)

    except KeyboardInterrupt:
        pass
    finally:
        print("Shutting down")
        rfm69.shutdown()
