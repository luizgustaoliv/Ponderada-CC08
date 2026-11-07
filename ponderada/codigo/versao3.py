"""A4, versao 3: produtor adquire mutex antes de vazio e permite deadlock."""

import multiprocessing
from experimento import main

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main(3)
