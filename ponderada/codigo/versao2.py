"""A4, versao 2: produtor-consumidor com vazio, cheio e mutex, nessa ordem."""

import multiprocessing
from experimento import main

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main(2)
