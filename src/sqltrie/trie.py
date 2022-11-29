from collections.abc import MutableMapping
from abc import abstractmethod


class ShortKeyError(KeyError):
    """Raised when given key is a prefix of an existing longer key
    but does not have a value associated with itself."""


class AbstractTrie(MutableMapping):
    def __init__(self, *args, **kwargs):
        self.update(*args, **kwargs)

    def enable_sorting(self, enable=True):
        raise NotImplementedError

    def clear(self):
        raise NotImplementedError

    def update(self, *args, **kwargs):  # pylint: disable=arguments-differ
        raise NotImplementedError

    def merge(self, other, overwrite=False):
        raise NotImplementedError

    def copy(self, __make_copy=lambda x: x):
        raise NotImplementedError

    def __copy__(self):
        return self.copy()

    def __deepcopy__(self, memo):
        return self.copy(lambda x: _copy.deepcopy(x, memo))

    @classmethod
    def fromkeys(cls, keys, value=None):
        raise NotImplementedError

    def __iter__(self):
        return self.iterkeys()

    def iteritems(self, prefix=None, shallow=False):
        raise NotImplementedError

    def iterkeys(self, prefix=None, shallow=False):
        raise NotImplementedError

    def itervalues(self, prefix=None, shallow=False):
        raise NotImplementedError

    def items(self, prefix=None, shallow=False):
        return list(self.iteritems(prefix=prefix, shallow=shallow))

    def keys(self, prefix=None, shallow=False):
        return list(self.iterkeys(prefix=prefix, shallow=shallow))

    def values(self, prefix=None, shallow=False):
        return list(self.itervalues(prefix=prefix, shallow=shallow))

    def __len__(self):
        raise NotImplementedError

    def __bool__(self):
        raise NotImplementedError

    __nonzero__ = __bool__
    __hash__ = None

    def has_node(self, key):
        raise NotImplementedError

    def has_key(self, key):
        return bool(self.has_node(key) & self.HAS_VALUE)

    def has_subtrie(self, key):
        return bool(self.has_node(key) & self.HAS_SUBTRIE)

    def __getitem__(self, key_or_slice):
        raise NotImplementedError

    def __setitem__(self, key_or_slice, value):
        raise NotImplementedError

    def __delitem__(self, key_or_slice):
        raise NotImplementedError

    def setdefault(self, key, default=None):
        raise NotImplementedError

    def pop(self, key, default=None):
        raise NotImplementedError

    def popitem(self):
        raise NotImplementedError

    def walk_towards(self, key):
        raise NotImplementedError

    def prefixes(self, key):
        raise NotImplementedError

    def shortest_prefix(self, key):
        raise NotImplementedError

    def longest_prefix(self, key):
        raise NotImplementedError

    def traverse(self, node_factory, prefix=None):
        pass

