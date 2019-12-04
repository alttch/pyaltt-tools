"""
Requires neotermcolor
"""
import logging
import logging.handlers
import platform
import neotermcolor

from .network import parse_host_port

from types import SimpleNamespace

config = SimpleNamespace(
        log_file=None, # log file to write to
        log_stdout=2, # 0 - do not log, 1 - log, 2 - log auto
        syslog=None,
        level=10,
        tracebacks=False, # log exception tracebacks
        ignore=None, # ignore symbol
        stdout_ignore=True, # use ignore symbol for stdout
        keep_logmem=0,
        colorize=True, # colorize STDOUT records if possible
        formatter = logging.Formatter('%(asctime)s ' + platform.node() + \
            ' %(levelname)s f:%(filename)s mod:%(module)s fn:%(funcName)s ' + \
            'l:%(lineno)d th:%(threadName)s :: %(message)s'),
        syslog_formatter = None
        )

__data = SimpleNamespace(logger=None)

neotermcolor.set_style('logger:10', color='grey', attrs='bold')
neotermcolor.set_style('logger:20')
neotermcolor.set_style('logger:30', color='yellow')
neotermcolor.set_style('logger:40', color='red')
neotermcolor.set_style('logger:50', color='red', attrs='bold')


class StdoutHandler(logging.StreamHandler):

    def emit(self, record):
        if not config.stdout_ignore or \
                config.ignore is None or \
                not record.getMessage().startswith(config.ignore):
            super().emit(record)

    def format(self, record):
        r = super().format(record)
        return neotermcolor.colored(r, style='logger:{}'.format(
            record.levelno)) if config.colorize else r


class DummyHandler(logging.StreamHandler):

    def emit(self, record):
        pass


def log_traceback():
    # TODO
    pass


def set_debug(debug=False):
    level = 10 if debug else config.level
    logging.basicConfig(level=level)
    if __data.logger:
        __data.logger.setLevel(level)


def init(**kwargs):
    """
    """
    for k, v in kwargs.items():
        if not hasattr(config, k):
            raise AttributeError('Invalid argument: {}'.format(k))
        setattr(config, k, v)

    logging.basicConfig(level=config.level)

    __data.logger = logging.getLogger()
    for h in __data.logger.handlers:
        __data.logger.removeHandler(h)
    has_handler = False
    if config.log_file:
        has_handler = True
        file_handler = logging.handlers.WatchedFileHandler(config.log_file)
        file_handler.setFormatter(config.formatter)
        __data.logger.addHandler(file_handler)
    # TODO: memory handler
    if config.syslog:
        has_handler = True
        if config.syslog is True:
            syslog_addr = '/dev/log'
        elif config.syslog.startswith('/'):
            syslog_addr = config.syslog
        else:
            addr, port = parse_host_port(config.syslog, 514)
            if addr:
                syslog_addr = (addr, port)
            else:
                logging.error('Invalid syslog configuration: {}'.format(
                    config.syslog))
                syslog_addr = None
        if syslog_addr:
            syslog_handler = logging.handlers.SysLogHandler(address=syslog_addr)
            syslog_handler.setFormatter(config.syslog_formatter if config.
                                        syslog_formatter else config.formatter)
            __data.logger.addHandler(syslog_handler)
    if (not has_handler and config.log_stdout == 2) or \
            config.log_stdout is True or config.log_stdout == 1:
        has_handler = True
        stdout_handler = StdoutHandler()
        stdout_handler.setFormatter(config.formatter)
        __data.logger.addHandler(stdout_handler)
    if not has_handler:
        # mute all logs
        __data.logger.addHandler(DummyHandler())
