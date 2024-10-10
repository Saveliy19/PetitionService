import logging

logger = logging.getLogger('master_logger')
logger.setLevel(logging.ERROR)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s')

file_handler = logging.FileHandler('app.log', encoding='utf-8')
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)