
import json
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
			sort_kwargs: bool = True,
			kwarg_sort_func: callable = sorted,
			accept_dict_args: bool = True,
			sort_dict_args: bool = True,
			dict_args_sort_func: callable = sorted,
			recurse_dict_args: bool = True,
			accept_dict_kwargs: bool = True,
	):
		self.results_cache = {}
		self.sort_kwargs = sort_kwargs
		self.kwarg_sort_func = kwarg_sort_func
		self.accept_dict_args = accept_dict_args
		self.sort_dict_args = sort_dict_args
		self.dict_args_sort_func = dict_args_sort_func
		self.recurse_dict_args = recurse_dict_args
		self.accept_dict_kwargs = accept_dict_kwargs

	def process_params(
			self, param_args: list, param_kwargs: dict
	) -> Tuple[Tuple[Any, ...], Tuple[Tuple[Any, Any], ...]]:
		'''
		Converts function parameters to a hashable form.

		See Memoizer.__init__ for processing options.

		Args:
			param_args (list): args to convert to a hashable form:
				Converted form is a tuple of arguments
			param_kwargs (dict): kwargs to convert to a hashable form:
				Converted form is a tuple of tuples of key-value pairs

		Returns:
			Tuple[Tuple[Any, ...], Tuple[Tuple[Any, Any], ...]]: A hashable
				tuple of args and kwargs.
		'''

		# Convert function parameters to a hashable form

		if self.accept_dict_args:
			processed_args = tuple([
				Memoizer._dict_to_hashable_if_dict(
					arg,
					sort_after=self.sort_dict_args,
					sort_func=self.dict_args_sort_func,
					recurse=self.recurse_dict_args,
				) for arg in param_args
			])
		else:
			processed_args = tuple(param_args)

		processed_kwargs = Memoizer.dict_to_hashable(
			param_kwargs,
			sort_after=self.sort_kwargs,
			sort_func=self.kwarg_sort_func,
			recurse=self.accept_dict_kwargs,
		)

		return (processed_args, processed_kwargs)

	def call_and_add_result(self, function: callable, *args, **kwargs) -> Any:
		result = function(*args, **kwargs)
		params = self.process_params(args, kwargs)
		self.results_cache[function][params] = result

	def clear_cache(self, function: callable) -> None:
		'''
		Convenience method to clear a function from the cache.

		Args:
			function (callable): Function to clear from cache.
		'''

		if function in self.results_cache:
			del self.results_cache[function]

	def get_result(self, function: callable, *args, **kwargs) -> Any:
		if function not in self.results_cache:
			self.results_cache[function] = {}

		params = self.process_params(args, kwargs)

		if params not in self.results_cache[function]:
			self.call_and_add_result(function, *args, **kwargs)

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

	@staticmethod
	def dict_to_hashable(
			dict_to_hash: dict,
			recurse: bool = False,
			sort_after: bool = False,
			sort_func: callable = sorted
	) -> Tuple[Tuple[Hashable, Hashable]]:
		'''
		Converts a dict to a tuple of tuples, such that it may be hashed.

		Args:
			dict_to_hash (dict): The dict that should be made hashable.
			recurse (bool, optional): Defaults to False. Whether to recurse
				down sub-dictionaries.
			sort_after (bool, optional): Defaults to False. Whether to sort
				the dict afterwards. If true, uses `sort_func`.
			sort_func (callable, optional): Defaults to `sorted`. Function to
				call on the dict to sort it.

		Returns:
			Tuple[Tuple[Hashable, Hashable]]
		'''

		if recurse:
			result = (
				(
					Memoizer._dict_to_hashable_if_dict(
						key, recurse=True, sort_after=sort_after, sort_func=sort_func
					),
					Memoizer._dict_to_hashable_if_dict(
						value, recurse=True, sort_after=sort_after, sort_func=sort_func
					)
				) for key, value in dict_to_hash.items()
			)
		else:
			result = ((key, value) for key, value in dict_to_hash.items())

		if sort_after:
			return tuple(sort_func(result))
		else:
			return result

	@staticmethod
	def _dict_to_hashable_if_dict(potential_dict: Any, **kwargs) -> Any:
		'''
		Helper function for `dict_to_hashable`. Calls `dict_to_hashable` on
			the `potential_dict` if it's a dict, returns it unchanged otherwise.

		Args:
			potential_dict (Any): Object that may or may not be a dict.

		Returns:
			Any: Either `potential_dict` or the results of `dict_to_hashable`.
		'''

		if isinstance(potential_dict, dict):
			return Memoizer.dict_to_hashable(potential_dict, **kwargs)
		else:
			return potential_dict


class OldMemoizer:
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
	'''

	def __init__(self):
		'''
		Inits a new Memoizer.
		'''

		self.functions = {}
		self.hits = 0
		self.misses = 0

	def get_result(self, function: callable, *args, assume_hashable_args=True, **kwargs) -> Any:
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
			Object: The return value of function.
		'''

		if function not in self.functions:
			self.functions[function] = {}

		if assume_hashable_args:
			params = (tuple(args), self.make_hashable(kwargs))
		else:
			params = (self.make_hashable(args), self.make_hashable(kwargs))

		if params in self.functions[function]:
			self.hits += 1
			return self.functions[function][params]
		else:
			self.misses += 1
			self.functions[function][params] = function(*args, **kwargs)
			return self.functions[function][params]

	@staticmethod
	def make_hashable(obj) -> Hashable:
		try:
			hash(obj)  # Isinstance Hashable fails on nested objects
			return obj
		except TypeError:
			if isinstance(obj, dict):
				return tuple(sorted((Memoizer.make_hashable((key, value)) for key, value in obj.items())))
			elif isinstance(obj, Iterable):
				return tuple((Memoizer.make_hashable(value) for value in obj))
			return json.dumps(obj)

