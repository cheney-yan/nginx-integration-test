#!/usr/bin/env python
import fire
import requests
import os
import sys
import logging
from time import sleep
import yaml
import dns.resolver

# from termcolor import colored
DEFAULT_LOG_FORMAT = ('%(levelname)s %(message)s')
DEFAULT_TIME_STAMP = "%m-%d %H:%M:%S"
BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)

# The background is set with 40 plus the number of the color, and the foreground with 30

# These are the sequences need to get colored ouput
RESET_SEQ = "\033[0m"
COLOR_SEQ = "\033[1;%dm"
BOLD_SEQ = "\033[1m"


def formatter_message(message, use_color=True):
    if use_color:
        message = message.replace(
            "$RESET", RESET_SEQ).replace("$BOLD", BOLD_SEQ)
    else:
        message = message.replace("$RESET", "").replace("$BOLD", "")
    return message


COLORS = {
    'WARNING': YELLOW,
    'INFO': WHITE,
    'DEBUG': BLUE,
    'CRITICAL': YELLOW,
    'ERROR': RED
}


class ColoredFormatter(logging.Formatter):
    def __init__(self, msg, use_color=True):
        logging.Formatter.__init__(self, msg, DEFAULT_TIME_STAMP)
        self.use_color = use_color

    def format(self, record):
        levelname = record.levelname
        if self.use_color and levelname in COLORS:
            levelname_color = COLOR_SEQ % (
                30 + COLORS[levelname]) + levelname + RESET_SEQ
            record.levelname = levelname_color
        return logging.Formatter.format(self, record)


class ColoredLogger(logging.Logger):
    FORMAT = DEFAULT_LOG_FORMAT
    COLOR_FORMAT = formatter_message(FORMAT, True)

    def __init__(self, name):
        logging.Logger.__init__(self, name, logging.DEBUG)

        color_formatter = ColoredFormatter(self.COLOR_FORMAT)

        console = logging.StreamHandler()
        console.setFormatter(color_formatter)

        self.addHandler(console)
        return


logging.setLoggerClass(ColoredLogger)


def get_logger(name, level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    return logger


logger = get_logger(__file__)


def refine_path(path):
    here = os.path.dirname(__file__)
    if path.startswith('~'):
        return os.path.expanduser(path)
    if not path.startswith('/'):
        return os.path.join(here, path)
    return path


resolved_ips = {}


def resolve_ip(expected):
    result = []
    for domain in expected:
        if domain not in resolved_ips:
            answers = [str(item) for item in dns.resolver.query(domain, 'A')]
            resolved_ips[domain] = answers
            result += answers
        else:
            result += resolved_ips[domain]
    return result


def matches(output_line, expected):
    if not output_line:
        logger.error("Output line is empty, something is wrong")
        exit(1)
    if not expected:
        logger.error("Expected output is empty! Illegal configuration!")
        exit(1)
    for e in expected:
        if 'to: %s' % e in output_line:
            logger.debug('Found match %s in "%s"', e, output_line)
            return True
    logger.warn('None of %s appears in "%s".', expected, output_line)
    return False


def test(test_config='test.yaml', input=None, log_level='WARN', sleep_sec=2):
    failed_count = 0
    if sleep_sec:
        sleep(sleep_sec)
    logger.setLevel(log_level)
    if input:
        input = open(refine_path(input))
    else:
        input = sys.stdin
    test_config = yaml.load(open(refine_path(test_config)))
    logger.debug('Loaded test config: %s', test_config)
    for test_item in test_config:
        logger.info("Testing %s:%s", test_item['id'], test_item['comment'])
        i = test_item['input']
        url = "{schema}://{domain}{path}".format(
            schema=i.get('schema', 'http'),
            domain=i['domain'],
            path=i.get('path', '/')
        )
        logger.debug(
            "Method: {method}, URL: {url}, Params: {params}, Cookies: {cookies}, Headers: {headers}".format(
                method=i.get('method', 'GET'),
                url=url,
                cookies=i.get('cookies', {}),
                headers=i.get('headers', {}),
                params=i.get('params', {})
            )
        )
        try:
            requests.request(i.get('method', 'GET'), url, cookies=i.get(
                'cookies', {}), headers=i.get('headers', {}), params=i.get('params', {}))
            input_line = input.readline()
            if matches(input_line, resolve_ip(test_item['output'])):
                logger.info('%s PASSED', test_item['id'])
            else:
                logger.error("%s FAILED", test_item['id'])
                failed_count += 1
        except Exception as e:
            logger.exception(e)
            logger.error("%s FAILED", test_item['id'])
            failed_count += 1
    exit(failed_count)


if __name__ == '__main__':
    fire.Fire(test)
