"""A4, versao 1: buffer circular sem sincronizacao, com corrida no contador."""

import multiprocessing
from experimento import main

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main(1)
