
from collections import deque

from rememo import Memoizer


class LRUCache(Memoizer):
	'''
	Memoizer with a basic LRU cache.
	Attributes:
		max_cache_size (int): Maximum size of the cache, by item count
		cache_queue (collections.deque): Queue for tracking LRU cache
	'''

	def __init__(self, max_cache_size: int = 100, **kwargs):
		self.max_cache_size = max_cache_size
		self.cache_queue = deque()
		# TODO: Replace deque with DLL + Hashmap for efficient ops

		super().__init__(**kwargs)

	def handle_cache_decay(self, function: callable, params: tuple, was_hit: bool) -> None:
		fp = (function, params)
		if was_hit:
			self.cache_queue.remove(fp)
		self.cache_queue.append(fp)

		if len(self.cache_queue) > self.max_cache_size:
			old_func, old_params = self.cache_queue.popleft()
			del self.results_cache[old_func][old_params]

		super().handle_cache_decay(function, params, was_hit)

