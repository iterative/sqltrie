import json
from abc import abstractmethod
from typing import Any, Optional

from .trie import AbstractTrie, Iterator, TrieKey


class SerializedTrie(AbstractTrie):
    @property
    @abstractmethod
    def _trie(self):
        pass

    @abstractmethod
    def _load(self, key: TrieKey, value: Optional[bytes]) -> Optional[Any]:
        pass

    @abstractmethod
    def _dump(self, key: TrieKey, value: Optional[Any]) -> Optional[bytes]:
        pass

    def __setitem__(self, key, value):
        self._trie[key] = self._dump(key, value)

    def __getitem__(self, key):
        raw = self._trie[key]
        return self._load(key, raw)

    def __delitem__(self, key):
        del self._trie[key]

    def __len__(self):
        return len(self._trie)

    def view(self, key: Optional[TrieKey] = None) -> "SerializedTrie":
        if not key:
            return self

        raw_trie = self._trie.view(key)
        trie = type(self)()
        # pylint: disable-next=protected-access
        trie._trie = raw_trie  # type: ignore
        return trie

    def items(self, *args, **kwargs):
        yield from (
            (key, self._load(key, raw))
            for key, raw in self._trie.items(*args, **kwargs)
        )

    def ls(self, key):
        yield from self._trie.ls(key)

    def traverse(self, node_factory, prefix=None):
        def _node_factory_wrapper(path_conv, path, children, value):
            return node_factory(
                path_conv, path, children, self._load(path, value)
            )

        return self._trie.traverse(_node_factory_wrapper, prefix=prefix)

    def diff(self, *args, **kwargs):
        yield from self._trie.diff(*args, **kwargs)

    def has_node(self, key):
        return self._trie.has_node(key)

    def shortest_prefix(self, key):
        skey, raw = self._trie.shortest_prefix(key)
        return key, self._load(skey, raw)

    def longest_prefix(self, key):
        lkey, raw = self._trie.longest_prefix(key)
        return lkey, self._load(lkey, raw)

    def __iter__(self) -> Iterator[TrieKey]:
        yield from self._trie


class JSONTrie(SerializedTrie):  # pylint: disable=abstract-method
    def _load(self, key: TrieKey, value: Optional[bytes]) -> Optional[Any]:
        if value is None:
            return None
        return json.loads(value.decode("utf-8"))

    def _dump(self, key: TrieKey, value: Optional[Any]) -> Optional[bytes]:
        if value is None:
            return None
        return json.dumps(value).encode("utf-8")
