import os
import logging
from flask import g
from logging.handlers import TimedRotatingFileHandler


class CustomLogger:
    def __init__(self, name: str, loglevel=logging.INFO):
        """Initialize the CustomLogger class

        Args:
            name (str): the name of the logger (e.g., __name__).
            loglevel (_type_, optional): the log level. Defaults to logging.INFO.
        """
        # Create a custom logger
        self.logger = logging.getLogger("FactCheck")
        self.logger.setLevel(loglevel)
        # Create a handler for writing to the log file
        if not os.path.exists("./log"):
            # If the directory does not exist, create it
            os.makedirs("./log")
        env = os.environ.get("env", "dev")
        fh = TimedRotatingFileHandler(filename="./log/factcheck_{}.log".format(env), when="D", encoding="utf-8")
        fh.setLevel(loglevel)
        if not self.logger.handlers:
            # Create another handler for output to the console
            ch = logging.StreamHandler()
            ch.setLevel(loglevel)
            # Define the output format of the handler
            formatter = logging.Formatter("[%(levelname)s]%(asctime)s %(filename)s:%(lineno)d: %(message)s")
            fh.setFormatter(formatter)
            ch.setFormatter(formatter)
            # Add handler to logger
            self.logger.addHandler(fh)
            self.logger.addHandler(ch)

    def getlog(self):
        return self.logger
