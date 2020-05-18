#!/usr/local/python27/bin/python
#-*- encoding: utf-8 -*-
# by df on 2017-09-06
# use the same config as log4cpp lib
#
# /xxx/log/
# `-- 2017-09-01
#    |-- xxx.log
#    |-- xxx.log.1
#    `-- xxx.log.2
# `-- 2017-09-02
#    |-- xxx.log
#    |-- xxx.log.1
#    `-- xxx.log.2

import ConfigParser
import logging
import time, os
import errno
from logging.handlers import RotatingFileHandler

#global
log_default_root = '__default__'
log_file_format = '%(asctime)s <%(levelname)-5s><%(name)s:%(process)d><%(filename)s:%(lineno)d>%(message)s'
log_stderr_format =  '$COLOR$BOLD<%(levelname)-5s><%(name)s:%(process)d:%(threadName)s>$RESET$COLOR<%(filename)s:%(lineno)d>%(message)s'
log_simple_stderr_format = '%(asctime)s <%(levelname)-5s><%(name)s:%(process)d:%(threadName)s><%(filename)s:%(lineno)d>%(message)s'


BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)
RESET_SEQ = "\033[0m"
#COLOR_SEQ = "\033[1;%dm"         # color & bold
COLOR_SEQ = "\033[0;%dm"        # color only
BOLD_SEQ = "\033[1m" 

COLORS={
	'WARNING':WHITE,
	'INFO':YELLOW,
	'DEBUG':GREEN,
	'CRITICAL':YELLOW,
	'ERROR':RED,
	'RED':RED,
	'GREEN':GREEN,
	'YELLOW':YELLOW,
	'BLUE':BLUE,
	'MAGENTA':MAGENTA,
	'CYAN':CYAN,
	'WHITE':WHITE,}
"""
COLORS = {
	'INFO': YELLOW,
	'DEBUG': GREEN,
	'ERROR': RED } 
	"""

class ColoredFormatter(logging.Formatter):
	def __init__(self, *args, **kwargs):
		logging.Formatter.__init__(self, *args, **kwargs)

	def format(self, record):
		levelname = record.levelname
		color     = COLOR_SEQ % (30 + COLORS[levelname])
		message   = logging.Formatter.format(self, record)
		#print "1--" + repr(message)
		message   = message.replace("$RESET", RESET_SEQ)\
				.replace("$BOLD",  BOLD_SEQ)\
				.replace("$COLOR", color)
		#print "2--" + repr(message)
		#for k,v in COLORS.items():
		#	message = message.replace("$" + k,    COLOR_SEQ % (v+30))\
		#			.replace("$BG" + k,  COLOR_SEQ % (v+40))\
		#			.replace("$BG-" + k, COLOR_SEQ % (v+40))
		#print "3--" + repr(message)
		return message + RESET_SEQ

class DateRotatingFileHandler(RotatingFileHandler):
	def __init__(self , filename , mode='a' , maxBytes=0, backupCount=0, encoding=None):
		self.current = time.strftime("%Y%m%d" , time.localtime(time.time()))
		self.path = os.path.dirname(filename)
		#print self.path
		self.filename = os.path.basename(filename)
		newdir = os.path.join(self.path , self.current)
		if not os.access(newdir , os.X_OK):
			os.mkdir(newdir)
		newfile = os.path.join(newdir , self.filename)
		RotatingFileHandler.__init__(self, newfile , mode, maxBytes , backupCount , encoding)

	def doRollover(self):
		self.current = time.strftime("%Y%m%d" , time.localtime(time.time()))
		
		#repr() is not needed , time.strftime() return a string not a integer
		newdir = os.path.join(self.path , self.current)
		if not os.access(newdir , os.X_OK):
			try:
				os.mkdir(newdir)
			except OSError, e:
				if e.errno != errno.EEXIST:
					raise
		self.stream.close()
		self.baseFilename = os.path.join(newdir , self.filename)

		if self.encoding:
			self.stream = codecs.open(self.baseFilename, 'w', self.encoding)
		else:
			self.stream = open(self.baseFilename, 'w')

	def shouldRollover(self, record):
		if RotatingFileHandler.shouldRollover(self , record):
			RotatingFileHandler.doRollover(self)

		t = time.strftime("%Y%m%d" , time.localtime(time.time()))
		if (cmp(self.current , t) < 0) :
			return 1

		return 0


def init_log(prefix, cfg_file, type, level, log_file_fmt=None):
	global log_default_root, log_file_format, log_stderr_format

	if not log_file_fmt:
		log_file_fmt = log_file_format

	cf = ConfigParser.ConfigParser()
	cf.read(cfg_file)
	config = {}


	try:
		config['level'] = cf.get(prefix, 'level')
	except:
		config['level'] = cf.get(log_default_root, 'level')

	try:
		config['file_name'] = cf.get(prefix, 'file_name')
	except:
		config['file_name'] = cf.get(log_default_root, 'file_name')

	config['file_name'] = config['file_name'].replace('%name', prefix)
	config['file_name'] = config['file_name'].replace('%pid', str(os.getpid()))

	try:
		config['stderr'] = cf.getint(prefix, 'stderr')
	except:
		config['stderr'] = cf.getint(log_default_root, 'stderr')

	try:
		config['syslog'] = cf.getint(prefix, 'syslog')
	except:
		config['syslog'] = cf.getint(log_default_root, 'syslog')

	try:
		config['file_path'] = cf.get(prefix, 'file_path')
	except:
		config['file_path'] = cf.get(log_default_root, 'file_path')

	try:
		config['file_sizeMB'] = cf.getint(prefix, 'file_sizeMB')
	except:
		config['file_sizeMB'] = cf.getint(log_default_root, 'file_sizeMB')

	try:
		config['file_num'] = cf.getint(prefix, 'file_num')
	except:
		config['file_num'] = cf.getint(log_default_root, 'file_num')

	config['file_num'] = config['file_num'] - 1
	if config['file_num'] <= 0:
		config['file_num'] = 0

	print config

	#new a root logger
	logger = logging.getLogger(prefix)
	#set root logger level
	if config['level'] == 'debug':
		logger.setLevel(logging.DEBUG)
	elif config['level'] == 'info':
		logger.setLevel(logging.INFO)
	else:
		logger.setLevel(logging.ERROR)
	#new a log file handle
	log_handler = DateRotatingFileHandler(config['file_path'] + '/' + config['file_name'], mode="a", maxBytes = config['file_sizeMB']*1024*1024, backupCount=config['file_num'])
	#set log file handle format
	formatter = logging.Formatter(log_file_fmt, datefmt='%F %T')
	log_handler.setFormatter(formatter)
	#add to root logger
	logger.addHandler(log_handler)
	#new a stderr logger if need
	if not config['stderr']:
		return logger
	else:

		formatter = ColoredFormatter(log_stderr_format)
		#formatter = logging.Formatter(log_stderr_format)
		log_handler = logging.StreamHandler()
		log_handler.setFormatter(formatter)
		logger.addHandler(log_handler)
		return logger
	

def init_simple_log(prefix, level = 'info'):
	global log_stderr_format
	logger = logging.getLogger(prefix)
	if level == 'debug':
		logger.setLevel(logging.DEBUG)
	elif level == 'info':
		logger.setLevel(logging.INFO)
	else:
		logger.setLevel(logging.ERROR)
	formatter = logging.Formatter(log_file_format, datefmt='%F %T')
	log_handler = logging.StreamHandler()
	log_handler.setFormatter(formatter)
	logger.addHandler(log_handler)
	return logger

if __name__ == '__main__':
	global logger

	logger = init_log('test', '/root/PICK/pybin/config/Log.cfg', 0, 0)
	logger.debug('daifengtest123456789')
	logger.info('daifengtest123456789')
	logger.error('daifengtest123456789')

