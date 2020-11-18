
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

		super(type(self), self).__init__(*args, **kwargs)

	@classmethod
	def with_superclass_factory(
			cls,
			new_superclass: type,
			new_name: Optional[str] = None
	) -> type:
		'''
		Create a Tracking version of `new_superclass`. For example, passing in
			`Memoizer` for the `new_superclass` will provide a functionally
			identical duplicate of the default TrackingMemoizer, which already
			inherits from Memoizer.
		Don't pass a TrackingX to new_superclass unless you want a recursion error.

		Args:
			new_superclass (type): The new superclass from which to create a
				Tracking subclass
			new_name (str, optional): The name for the resulting subclass.
				Defaults to _Tracking__{SuperclassName}

		Returns:
			type: The new Tracking subclass.
		'''

		if new_name is None:
			new_name = f'_Tracking__{new_superclass.__name__}'

		return type(new_name, (new_superclass, ), dict(cls.__dict__))

	@classmethod
	def get_tracking_instance(cls, of_class: type, *args, **kwargs) -> object:
		'''
		Helper function for when you only need one instance of a Tracking version
			of a class. Gets the new Tracking subclass from `with_superclass_factory`
			and instantiates it with the provided args.

		Args:
			of_class (type): The new superclass from which to create a Tracking
				subclass instance
			*args: Variable length argument list. Passed to new class instantiation.
			**kwargs: Arbitrary keyword arguments. Passed to new class instantiation.

		Returns:
			object: The new Tracking subclass instance.
		'''

		return cls.with_superclass_factory(of_class)(*args, **kwargs)

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
			function (callable, optional):
				If provided, the function to retrieve the hits and misses for.
				If omitted, instead retrieves hits and misses overall.

		Returns:
			Tuple[int, int]: A tuple of (hits, misses)
		'''

		if function is not None:
			return (self.hits_by_func[function], self.misses_by_func[function])
		else:
			return (self.hits_total, self.misses_total)
