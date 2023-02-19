
import unittest
import logging
import multiprocessing.managers

import rememo
from rememo.templates.shared import RemoteCache

from tests import test_Memoizer

logger = logging.getLogger(__name__)


class TestRemoteCache(unittest.TestCase):
	def test_create(self):
		cache = RemoteCache()
		cache2 = RemoteCache()
		self.assertTrue(cache.is_host)
		self.assertFalse(cache2.is_host)

	def test_host_failover(self):
		cache = RemoteCache()
		cache2 = RemoteCache()
		self.assertTrue(cache.is_host)
		self.assertFalse(cache2.is_host)
		del cache
		cache2.ping()
		self.assertTrue(cache2.is_host)

	def test_set_get(self):
		cache = RemoteCache()
		cache['key'] = 3
		self.assertEqual(cache['key'], 3)
		with self.assertRaises(multiprocessing.managers.RemoteError):
			cache['unset_key']

	def test_get_shared(self):
		cache = RemoteCache()
		cache['key'] = 'val'
		cache2 = RemoteCache()
		self.assertEqual(cache2['key'], 'val')

	def test_preprocess_key(self):
		def preprocessor(key):
			return key[::-1]
		cache = RemoteCache(key_preprocessor=preprocessor)
		cache['key'] = 'val'
		self.assertEqual(cache['key'], 'val')
		self.assertEqual(cache.manager['yek']._getvalue(), 'val')
		cache2 = RemoteCache()
		self.assertEqual(cache2['yek'], 'val')


class TestSharedMemoizer(test_Memoizer.TestMemoizer):
	def setUp(self):
		self.memoizer = rememo.SharedMemoizer()
