
import unittest
import logging

import rememo

from tests import test_Memoizer

logger = logging.getLogger(__name__)


class TestRemoteCache(unittest.TestCase):
	pass


class TestSharedMemoizer(test_Memoizer.TestMemoizer):
	def setUp(self):
		self.memoizer = rememo.SharedMemoizer()
