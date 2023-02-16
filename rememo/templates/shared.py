
import logging

from multiprocessing.managers import SyncManager
from typing import Optional, Tuple, Any
from functools import wraps

from rememo import Memoizer

logger = logging.getLogger(__name__)


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
		self._connect_or_establish_manager(address, authkey)

	def _connect_or_establish_manager(self, address, authkey):
		self.manager = SyncManager(address=address, authkey=authkey)
		self.manager.register('__getitem__', self.cache.__getitem__)
		self.manager.register('__setitem__', self.cache.__setitem__)
		self.manager.register('__delitem__', self.cache.__delitem__)
		self.manager.register('__contains__', self.cache.__contains__)
		self.manager.register('__reversed__', self.cache.__reversed__)
		self.manager.register('__iter__', self.cache.__iter__)
		self.manager.register('__str__', self.cache.__str__)
		self.manager.start()


class RemoteCacheWrapper:
	def __init__(
			self,
			key_preprocessor: callable = lambda v: v,
			address: Tuple[str, int] = ('localhost', 50000),
			authkey: Optional[bytes] = None,
	):
		self.key_preprocessor = key_preprocessor
		self.address = address
		self.authkey = authkey
		self._connect_or_establish_manager(address, authkey)

	def create_server(self, address, authkey):
		logger.info(f'Establishing cache server at address {address}.')
		self.cache_server = CacheServer(
			address=address,
			authkey=authkey,
		)

	def _connect_or_establish_manager(self, address, authkey):
		try:
			self._connect(address, authkey)
		except ConnectionRefusedError as _:
			logger.warn(f'Failed to connect to cache server at address {address}.')
			logger.warn(f'Attempting to create new cache server.')
			self.create_server(address, authkey)
			self._connect(address, authkey)

	def _connect(self, address, authkey):
		logger.info(f'Connecting to cache server at address {address}.')
		self.manager = SyncManager(address=address, authkey=authkey)
		self.manager.register('__getitem__')
		self.manager.register('__setitem__')
		self.manager.register('__delitem__')
		self.manager.register('__contains__')
		self.manager.connect()
		logger.info('Connected.')

	def _handle_remote_call(preprocess_key: bool = True):
		"""
		Decorator that provides exception handling and key preprocessing for
		functions called on the cache manager.

		Functions wrapped in this decorator will, upon receiving a
		ConnectionRefusedError, attempt to reconnect to the cache manager. If
		*that* fails, the RemoteCacheWrapper will attempt to create a new cache
		manager and connect to that. If that *also* fails, an exception will be
		raised.

		Args:
			preprocess_key (bool, optional): Whether this method should
				preprocess the key, which must be the first argument to the
				method. Defaults to True.
		"""
		def _handle_remote_call_decorator(function):
			@wraps(function)
			def remote_call_wrapper(self, *args, **kwargs) -> Any:
				if preprocess_key is True:
					args = (self.key_preprocessor(args[0]), *args[1:])
				try:
					return function(self, *args, **kwargs)
				except ConnectionRefusedError as e:
					logger.warn(f'Failed to call {function} on cache server: {e}')
					self._connect_or_establish_manager(self.address, self.authkey)
					return function(self, *args, **kwargs)
			return remote_call_wrapper
		return _handle_remote_call_decorator

	@_handle_remote_call(preprocess_key=True)
	def __getitem__(self, key):
		return self.manager[key]._getvalue()

	@_handle_remote_call(preprocess_key=True)
	def __setitem__(self, key, value):
		self.manager[key] = value

	@_handle_remote_call(preprocess_key=True)
	def __delitem__(self, key):
		del self.manager[key]

	@_handle_remote_call(preprocess_key=True)
	def __contains__(self, key):
		return self.manager.__contains__(key)._getvalue()

	@_handle_remote_call(preprocess_key=False)
	def __str__(self):
		return self.manager.__str__()._getvalue()


class SharedMemoizer(Memoizer):
	'''
	Memoizer that can be shared across multiple processes
		Uses multiprocessing.Manager
	Attributes:
		results_cache: A RemoteCacheWrapper instance.
			This functions (nearly) identically to the results_cache on
			a standard Memoizer, but is actually a wrapper that allows
			access to a local or remote cache hosted by a CacheServer.
	'''

	def __init__(
			self,
			serialize_function_method: callable = serialize_function,
			address: Tuple[str, int] = ('localhost', 50000),
			authkey: bytes = b'',
			**kwargs
	):
		super().__init__(**kwargs)
		self.results_cache = RemoteCacheWrapper(
			key_preprocessor=serialize_function_method,
			address=address,
			authkey=authkey
		)

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

	def remove_from_cache(self, function: callable, *args, **kwargs) -> None:
		'''
		Clears a result or all results for a function from the cache.
		As with _call_and_add_result, we have to override this to work with
		RemoteCacheWrappers properly
		'''

		wrapped_func = getattr(function, '__wrapped__', None)
		if args or kwargs:
			params = self.process_params(args, kwargs)
			if function in self.results_cache and params in self.results_cache[function]:
				logger.debug(f'Removing unwrapped function {function} with params {params} from cache')
				local = self.results_cache[function]
				del local[params]
				self.results_cache[function] = local
			elif wrapped_func in self.results_cache and params in self.results_cache[wrapped_func]:
				logger.debug(f'Removing wrapped function {function} with params {params} from cache')
				local = self.results_cache[wrapped_func]
				del local[params]
				self.results_cache[wrapped_func] = local
			else:
				raise KeyError(f'Function {function} with params {params} not in cache')
		else:
			if function in self.results_cache:
				logger.debug(f'Removing unwrapped function {function} from cache')
				del self.results_cache[function]
			elif wrapped_func in self.results_cache:
				logger.debug(f'Removing wrapped function {function} from cache')
				del self.results_cache[wrapped_func]
			else:
				raise KeyError(f'Function {function} not in cache')
