
import pickle
from typing import Iterable, Any, Hashable, Tuple, Optional
from functools import wraps


class Memoizer:
	'''
	Class to facilitate memoization of function returns.

	Attributes:
		functions (
			Dict[
				callable: Dict[
					Tuple[frozenset, frozenset]: Object
				]
			]
		)
		A dictionary of functions: dictionary of args: results

	Methods:
		get_result: Gets the result of a function call, either
			by returning the stored result or by running the
			function if no stored results are found.

		memoized: Decorator to memoize a function. Causes the
			function to be called through get_result always.
	'''

	def __init__(
			self,
			make_hashable_func: callable = pickle.dumps,
			sort_kwargs: bool = True,
			kwarg_sort_func: callable = sorted,
			**kwargs
	):
		self.results_cache = {}

		self.make_hashable_func = make_hashable_func
		self.sort_kwargs = sort_kwargs
		self.kwarg_sort_func = kwarg_sort_func

	def process_params(
			self, param_args: list, param_kwargs: dict
	) -> Hashable:
		'''
		Converts function parameters to a hashable form.
		By default, this uses pickle.dumps

		See Memoizer.__init__ for processing options.

		Args:
			param_args (list): args to convert to a hashable form
			param_kwargs (dict): kwargs to convert to a hashable form

		Returns:
			Hashable: A hashable form of the input parameters.
				For the default method of pickle.dumps, this is a bytes object
		'''

		return self.make_hashable_func((param_args, param_kwargs))

	def _call_and_add_result(self, function: callable, *args, **kwargs) -> None:
		'''
		Calls the function and adds it to the cache.

		Args:
			function (callable): The function to run.
			*args: Variable length argument list. Passed to function.
			**kwargs: Arbitrary keyword arguments. Passed to function.
		'''

		result = function(*args, **kwargs)
		params = self.process_params(args, kwargs)
		self.results_cache[function][params] = result

	def remove_from_cache(self, function: callable, params: Optional[tuple] = None) -> None:
		'''
		Convenience method to clear a result or all results for a function from the cache.

		Args:
			function (callable): Function to clear from cache.
			params (tuple, optional): A set of parameters for that function.
				If provided, only the results for this set of params will be cleared.
				If omitted, the results for all param sets for that function will be cleared.
		'''

		if params is not None:
			if function in self.results_cache and params in self.results_cache[function]:
				del self.results_cache[function][params]
		else:
			if function in self.results_cache:
				del self.results_cache[function]

	def handle_cache_decay(self, function: callable, params: tuple, was_hit: bool) -> None:
		'''
		Placeholder for handling cache changes. Subclasses should override this.

		Args:
			function (callable): Function called
			params (tuple): Parameters to the call
			was_hit (bool): Whether the call was a cache hit
		'''

		pass

	def get_result(self, function: callable, *args, **kwargs) -> Any:
		'''
		Gets the result of a function call with specific arguments.
		If the function has been called through get_result before with these
			parameters in this Memoizer, this will return the memoized result.
		Otherwise, it will run the function and memoize the new result.

		Args:
			function (callable): The function to run.
				This should *always* be idempotent or nullipotent.
			*args: Variable length argument list. Passed to function.
			**kwargs: Arbitrary keyword arguments. Passed to function.

		Returns:
			Any: The return value of function.
		'''

		if function not in self.results_cache:
			self.results_cache[function] = {}

		params = self.process_params(args, kwargs)

		if params not in self.results_cache[function]:
			self._call_and_add_result(function, *args, **kwargs)
			self.handle_cache_decay(function, params, was_hit=False)
		else:
			self.handle_cache_decay(function, params, was_hit=True)

		return self.results_cache[function][params]

	def memoized(self, function: callable) -> callable:
		'''
		Decorator for memoizing functions. Should only be used with idem- or
			nullipotent functions.

		Args:
			function (callable): Function to be memoized.

		Returns:
			callable: Wrapper function to get cached results when possible.
				Adds the results to the cache if not already in there.

		Aliases:
			Memoizer.memo, Memoizer.cache
		'''

		@wraps(self.get_result)
		def get_result_wrapper(*args, **kwargs) -> Any:
			return self.get_result(function, *args, **kwargs)

		return get_result_wrapper
	memo = memoized
	cache = memoized

