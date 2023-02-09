#!/usr/bin/env python3


import unittest
import logging
import sys
import os

logger = logging.getLogger(__name__)


if __name__ == '__main__':
	sys.path.append(os.path.dirname(os.path.dirname(__file__)))
	verbosity = 1
	if ('-v' in sys.argv) or ('--verbose' in sys.argv):
		logging.basicConfig(level=logging.INFO, format='    %(funcName)s %(message)s')
		verbosity = 2
	if ('-vv' in sys.argv) or ('--very-verbose' in sys.argv):
		logging.basicConfig(level=logging.DEBUG, format='    %(funcName)s %(message)s')
		verbosity = 3
	suite = unittest.TestLoader().discover('tests', pattern='test*.py')
	result = unittest.TextTestRunner(verbosity=verbosity).run(suite)
