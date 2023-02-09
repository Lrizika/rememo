
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
		def testfunc():
			return time.time()

		result = testfunc()
		second_result = testfunc()
		self.assertEqual(
			result,
			second_result
		)

		m.remove_from_cache(testfunc)
		print(m.results_cache)

		third_result = testfunc()
		self.assertNotEqual(
			result,
			third_result
		)


