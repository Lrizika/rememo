
import unittest
import logging
import time

import rememo

logger = logging.getLogger(__name__)


class TestMemoizer(unittest.TestCase):
	def test_memoizes(self):
		m = rememo.Memoizer()

		called_count = 0

		@m.memo
		def testfunc(val):
			nonlocal called_count
			called_count += 1
			return val + 2

		testfunc(5)
		self.assertEqual(
			called_count,
			1
		)
		testfunc(5)
		self.assertEqual(
			called_count,
			1
		)

	def test_in_results_cache(self):
		m = rememo.Memoizer()

		@m.memo
		def testfunc(val):
			return val + 2

		result = testfunc(5)
		self.assertEqual(
			m.get_result(testfunc, 5),
			result
		)

	def test_cache_removal(self):
		m = rememo.Memoizer()

		@m.memo
		def testfunc(v):
			return time.time(), v

		result_2_1 = testfunc(2)
		result_2_2 = testfunc(2)
		self.assertEqual(
			result_2_1,
			result_2_2
		)

		result_3_1 = testfunc(3)
		# Remove a function with a specific parameter from the cache
		m.remove_from_cache(testfunc, 2)

		result_2_3 = testfunc(2)
		self.assertNotEqual(
			result_2_1,
			result_2_3
		)

		result_3_2 = testfunc(3)
		self.assertEqual(
			result_3_1,
			result_3_2
		)
		# Remove a function entirely from the cache
		m.remove_from_cache(testfunc)

		result_3_3 = testfunc(3)
		self.assertNotEqual(
			result_3_1,
			result_3_3
		)


