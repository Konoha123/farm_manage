import logging
import typing

# 初始化日志模块
logging.basicConfig(level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S',
                    format='%(asctime)s.%(msecs)03d - %(levelname)s - %(name)s - line:%(lineno)d - %(message)s')

_default_level: int = logging.INFO


# 创建一个过滤器，根据不同的级别过滤日志
class LevelFilter(logging.Filter):
    def __init__(self,
                 name,
                 level):
        super().__init__(name)
        self.level = level

    def filter(self,
               record):
        return record.levelno >= self.level


class LoggerManager(object):
    def __init__(self,
                 level: int):
        self._level = level

    def get_logger(self,
                   name: typing.Optional[str] = None,
                   level: typing.Optional[int] = None) -> logging.Logger:
        if name is not None:
            if type(name) is not str:
                raise TypeError('name must be str')
        logger = logging.getLogger(name)
        level = self._level if level is None else level
        filterer = LevelFilter(name, level)
        logger.addFilter(filterer)
        logger.setLevel(level)
        return logger

    def set_level(self,
                  level: int):
        self._level = level


_manager = LoggerManager(_default_level)


def set_level(level: int):
    _manager.set_level(level)


def get_logger(name: typing.Optional[str] = None,
               level: typing.Optional[int] = None) -> logging.Logger:
    return _manager.get_logger(name, level)
