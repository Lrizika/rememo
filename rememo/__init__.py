
import logging

from rememo.memoizer import Memoizer
from rememo.templates import TrackingMemoizer, SharedMemoizer

logger = logging.getLogger(__name__)

default_memoizer = Memoizer()
memo = default_memoizer.memo
cache = default_memoizer.cache
memoized = default_memoizer.memoized
