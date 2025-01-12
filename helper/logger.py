import datetime
import logging
import os
from logging.handlers import RotatingFileHandler


class Logger:
    """
    Logger class for saving and printing logs
    """

    def __init__(self, log_directory=".logs"):
        if not os.path.exists(log_directory):
            os.makedirs(log_directory)
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H")
        log_filename = f"{log_directory}/log_{timestamp}.log"
        self.logger = logging.getLogger("AirbyteHackathon")
        self.logger.setLevel(logging.INFO)

        file_handler = RotatingFileHandler(
            log_filename, maxBytes=1024 * 1024, backupCount=5
        )
        log_fmt = "%(asctime)s - %(levelname)s - %(message)s"
        formatter = logging.Formatter(log_fmt)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(log_fmt))
        self.logger.addHandler(console_handler)

    def get_logger(self):
        return self.logger
