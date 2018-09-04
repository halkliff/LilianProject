import logging
import os
import datetime
import sys

logger = logging.getLogger('MAIN')
# file_logger = logging.FileHandler(os.path.abspath('logs/log_%s.log' % datetime.date.today()))
# file_logger.setLevel(logging.ERROR)
console_logger = logging.StreamHandler(sys.stderr)
console_logger.setLevel(logging.INFO)
formatter = logging.Formatter(
    "%(asctime)s (%(filename)s:%(lineno)d %(threadName)s) %(levelname)s - %(name)s: %(message)s"
)
# file_logger.setFormatter(formatter)
console_logger.setFormatter(formatter)
# logger.addHandler(file_logger)
logger.addHandler(console_logger)
logger.setLevel(logging.INFO)
