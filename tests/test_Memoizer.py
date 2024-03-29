
import unittest
import logging
import time

import rememo

logger = logging.getLogger(__name__)


class TestMemoizer(unittest.TestCase):
	def setUp(self):
		self.memoizer = rememo.Memoizer()

	def tearDown(self):
		del self.memoizer

	def test_memoizes(self):
		called_count = 0

		@self.memoizer.memo
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
		@self.memoizer.memo
		def testfunc(val):
			return val + 2

		result = testfunc(5)
		self.assertEqual(
			self.memoizer.get_result(testfunc, 5),
			result
		)

	def test_get_result(self):
		called_count = 0

		@self.memoizer.memo
		def testfunc(val):
			nonlocal called_count
			called_count += 1
			return val + 2

		testfunc(2)
		testfunc(2)
		self.memoizer.get_result(testfunc.__wrapped__, 2)
		self.assertEqual(called_count, 1)

		self.memoizer.get_result(testfunc.__wrapped__, 3)
		self.assertEqual(called_count, 2)

		self.memoizer.get_result(testfunc, 5)
		self.assertEqual(called_count, 3)

	def test_cache_removal(self):
		@self.memoizer.memo
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
		self.memoizer.remove_from_cache(testfunc, 2)

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
		self.memoizer.remove_from_cache(testfunc)

		result_3_3 = testfunc(3)
		self.assertNotEqual(
			result_3_1,
			result_3_3
		)


