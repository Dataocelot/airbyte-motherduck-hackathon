import datetime
import logging
import os
from logging.handlers import RotatingFileHandler

class Logger:
    def __init__(self, log_directory="logs"):
        if not os.path.exists(log_directory):
            os.makedirs(log_directory)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"{log_directory}/log_{timestamp}.log"
        self.logger = logging.getLogger("ApplianceScraperLogger")
        self.logger.setLevel(logging.INFO)

        handler = RotatingFileHandler(log_filename, maxBytes=5*1024, backupCount=5)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)

        self.logger.addHandler(handler)

    def get_logger(self):
        return self.logger
