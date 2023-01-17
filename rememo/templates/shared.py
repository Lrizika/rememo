
import marshal
import multiprocessing
from multiprocessing.managers import SyncManager
import pickle
from typing import Optional, Tuple

from rememo import Memoizer


# def serialize_function(function: callable) -> Tuple[bytes, bytes, bytes, bytes]:
# 	'''
# 	Serializes a function to a hashable tuple of bytestrings
# 	Used by SharedMemoizers as a default method of converting a callable to
# 	a pickleable hashable for usage as a key to the result cache
# 	'''
# 	marshalled_code = marshal.dumps(function.__code__)
# 	pickled_name = pickle.dumps(function.__name__)
# 	pickled_defaults = pickle.dumps(function.__defaults__)
# 	pickled_closure = pickle.dumps(function.__closure__)
# 	return (marshalled_code, pickled_name, pickled_defaults, pickled_closure)


def serialize_function(function: callable) -> str:
	'''
	Serializes a function to a hashable string
	In this case, a qualified name
	Used by SharedMemoizers as a default method of converting a callable to
	a pickleable hashable for usage as a key to the result cache
	'''
	return f'{function.__module__}.{function.__qualname__}'


class CacheServer:
	def __init__(
			self,
			address: Tuple[str, int] = ('localhost', 50000),
			authkey: Optional[bytes] = None,
	):
		self.cache = {}
		self._establish_manager(address, authkey)

	def _establish_manager(self, address, authkey):
		self.manager = SyncManager(address=address, authkey=authkey)
		self.manager.register('__getitem__', self.cache.__getitem__)
		self.manager.register('__setitem__', self.cache.__setitem__)
		self.manager.register('__delitem__', self.cache.__delitem__)
		self.manager.register('__contains__', self.cache.__contains__)
		self.manager.register('__reversed__', self.cache.__reversed__)
		self.manager.register('__iter__', self.cache.__iter__)
		self.manager.start()


class RemoteCacheWrapper:
	def __init__(
			self,
			key_preprocessor: callable = lambda v: v,
			address: Tuple[str, int] = ('localhost', 50000),
			authkey: Optional[bytes] = None,
	):
		self.key_preprocessor = key_preprocessor
		self._establish_manager(address, authkey)

	def _establish_manager(self, address, authkey):
		self.manager = SyncManager(address=address, authkey=authkey)
		self.manager.register('__getitem__')
		self.manager.register('__setitem__')
		self.manager.register('__delitem__')
		self.manager.register('__contains__')
		self.manager.connect()

	def __getitem__(self, key):
		key = self.key_preprocessor(key)
		return self.manager[key]._getvalue()

	def __setitem__(self, key, value):
		key = self.key_preprocessor(key)
		self.manager[key] = value

	def __delitem__(self, key):
		key = self.key_preprocessor(key)
		del self.manager[key]

	def __contains__(self, key):
		key = self.key_preprocessor(key)
		return self.manager.__contains__(key)._getvalue()

	# def __len__(self):
	# 	return len(self.cache)

	# def __iter__(self):
	# 	return iter(self.cache)

	# def __reversed__(self):
	# 	return reversed(self.cache)


# class RemoteCacheWrapper(multiprocessing.managers.DictProxy):
# 	def __init__(self, *args, key_preprocessor: callable, **kwargs) -> None:
# 		self.key_preprocessor = key_preprocessor
# 		super().__init__(*args, **kwargs)

# 	def __setitem__(self, key, value):
# 		key = self.key_preprocessor(key)
# 		return super().__setitem__(self, key, value)

# 	def __getitem__(self, key, value):
# 		key = self.key_preprocessor(key)
# 		return super().__getitem__(self, key, value)


class SharedMemoizer(Memoizer):
	'''
	Memoizer that can be shared across multiple processes
		Uses multiprocessing.Manager
	Attributes:
		TODO
	'''

	def __init__(
			self,
			serialize_function_method: callable = serialize_function,
			address: Tuple[str, int] = ('localhost', 50000),
			authkey: Optional[bytes] = None,
			**kwargs
	):
		super().__init__(**kwargs)
		try:
			print(f'Establishing cache server at address {address}.')
			self.cache_server = CacheServer(
				address=address,
				authkey=authkey,
			)
		except Exception as e:
			print(f'Server already exists at address {address}.')
		print(f'Connecting to cache server at address {address}.')
		self.results_cache = RemoteCacheWrapper(
			key_preprocessor=serialize_function_method,
			address=address,
			authkey=authkey
		)
		print('Connected.')

	def _call_and_add_result(self, function: callable, *args, **kwargs) -> None:
		'''
		Calls the function and adds it to the cache.
		Because of how RemoteCacheWrappers work, the standard
		results_cache[function][params] method does not work for SharedMemoizers -
		specifically, __getitem__ returns a local copy of the cache, and thus mutating
		values in it does not update them on the remote.
		'''

		result = function(*args, **kwargs)
		params = self.process_params(args, kwargs)
		new_cache = self.results_cache[function]
		new_cache[params] = result
		self.results_cache[function] = new_cache
