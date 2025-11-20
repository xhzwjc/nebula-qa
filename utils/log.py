import logging
import os
import time
from logging.handlers import TimedRotatingFileHandler

# 尝试导入 colorlog，如果不存在则降级处理
try:
    import colorlog
    HAS_COLORLOG = True
except ImportError:
    HAS_COLORLOG = False

class Logger:
    def __init__(self, logger_name='API_TEST'):
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.INFO)
        
        # 避免重复添加 handler
        if not self.logger.handlers:
            self._add_console_handler()
            self._add_file_handler()

    def _add_console_handler(self):
        if HAS_COLORLOG:
            log_colors = {
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
            formatter = colorlog.ColoredFormatter(
                '%(log_color)s[%(asctime)s] [%(levelname)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S',
                log_colors=log_colors
            )
        else:
            formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def _add_file_handler(self):
        # 确保 logs 目录存在
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        log_file = os.path.join(log_dir, f'api_test_{time.strftime("%Y%m%d")}.log')
        
        # 使用 TimedRotatingFileHandler 进行日志轮转
        file_handler = TimedRotatingFileHandler(
            filename=log_file,
            when='MIDNIGHT',
            interval=1,
            backupCount=7,
            encoding='utf-8'
        )
        
        formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(filename)s:%(lineno)d - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def get_logger(self):
        return self.logger

# 单例模式
logger = Logger().get_logger()

if __name__ == '__main__':
    logger.info("这是一条 info 日志")
    logger.warning("这是一条 warning 日志")
    logger.error("这是一条 error 日志")