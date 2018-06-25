from ener314 import rfm69


if __name__ == '__main__':
    try:
        rfm69.initialize()
        rfm69.blink()
        rfm69.blink()
        rfm69.blink()

    except KeyboardInterrupt:
        pass
    finally:
        rfm69.shutdown()
