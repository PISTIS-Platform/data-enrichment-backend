import logging
import os

def get_logger(name: str):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if logger.hasHandlers():
        logger.handlers.clear()

    stream_log_level = os.environ.get('STREAM_LOG_LEVEL', 'DEBUG').upper()
    file_log_level = os.environ.get('FILE_LOG_LEVEL', 'DEBUG').upper()

    stream_level = getattr(logging, stream_log_level, logging.WARNING)
    file_level = getattr(logging, file_log_level, logging.WARNING)

    # Stream handler
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(stream_level)
    stream_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    stream_handler.setFormatter(stream_formatter)
    logger.addHandler(stream_handler)

    # File handler
    file_handler = logging.FileHandler(f'logfile.log')
    file_handler.setLevel(file_level)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger