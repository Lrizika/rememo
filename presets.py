
from typing import Optional, Tuple

from memoizer import Memoizer


class TrackingMemoizer(Memoizer):
	'''
	Memoizer that tracks the number of cache hits and misses, both globally and
		per-function.

	Attributes:
		hits_total (int): Number of cache hits overall
		misses_total (int): Number of cache misses overall
		hits_by_func (Dict[callable: int]): Number of cache hits per-function
		misses_by_func (Dict[callable: int]): Number of cache misses per-function
	'''

	def __init__(self, *args, **kwargs):
		self.hits_total = 0
		self.misses_total = 0
		self.hits_by_func = {}
		self.misses_by_func = {}

		super().__init__(*args, **kwargs)

	def handle_cache_decay(self, function: callable, params: tuple, was_hit: bool) -> None:
		'''
		Handles changes to the cache. For TrackingMemoizer, updates hit and miss counts.

		Args:
			function (callable): Function called
			params (tuple): Parameters to the call
			was_hit (bool): Whether the call was a cache hit
		'''

		if function not in self.hits_by_func:
			self.hits_by_func[function] = 0
		if function not in self.misses_by_func:
			self.misses_by_func[function] = 0

		if was_hit:
			self.hits_total += 1
			self.hits_by_func[function] += 1
		else:
			self.misses_total += 1
			self.misses_by_func[function] += 1

		super().handle_cache_decay(self, function, params, was_hit)

	def get_hits_misses(self, function: Optional[callable] = None) -> Tuple[int, int]:
		'''
		Gets the number of hits and misses, either for a function or in total.

		Args:
			function (Optional[callable], optional):
				If provided, the function to retrieve the hits and misses for.
				If omitted, instead retrieves hits and misses overall.

		Returns:
			Tuple[int, int]: A tuple of (hits, misses)
		'''

		if function is not None:
			return (self.hits_by_func[function], self.misses_by_func[function])
		else:
			return (self.hits_total, self.misses_total)
