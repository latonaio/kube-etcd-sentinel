import os
import logging

from aion.logger import initialize_logger
from controller import Controller

SERVICE_NAME = os.environ.get("SERVICE_NAME")
KUBERNETES_PKG = "kubernetes"


def main():
    initialize_logger(SERVICE_NAME)
    logging.getLogger(KUBERNETES_PKG).setLevel(logging.ERROR)

    controller = Controller()
    controller.start()


if __name__ == "__main__":
    main()
