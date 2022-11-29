from abc import abstractmethod
from collections.abc import MutableMapping
from typing import Iterator, NamedTuple, Optional, Tuple, Union

from attrs import define


class ShortKeyError(KeyError):
    """Raised when given key is a prefix of an existing longer key
    but does not have a value associated with itself."""


TrieKey = Union[Tuple[()], Tuple[str]]


class TrieNode(NamedTuple):
    key: TrieKey
    value: Optional[bytes]


ADD = "add"
MODIFY = "modify"
RENAME = "rename"
DELETE = "delete"
UNCHANGED = "unchanged"


@define(frozen=True, hash=True, order=True)
class Change:
    typ: str
    old: Optional[TrieNode]
    new: Optional[TrieNode]

    @property
    def key(self) -> TrieKey:
        if self.typ == RENAME:
            raise ValueError

        if self.typ == ADD:
            entry = self.new
        else:
            entry = self.old

        assert entry
        assert entry.key
        return entry.key

    def __bool__(self) -> bool:
        return self.typ != UNCHANGED


class AbstractTrie(MutableMapping):
    def __init__(self, *args, **kwargs):
        self.update(*args, **kwargs)

    @abstractmethod
    def items(  # type: ignore
        self, prefix: Optional[TrieKey] = None, shallow: Optional[bool] = False
    ) -> Iterator[Tuple[TrieKey, bytes]]:
        pass

    @abstractmethod
    def view(self, key: Optional[TrieKey] = None) -> "AbstractTrie":
        pass

    @abstractmethod
    def has_node(self, key: TrieKey) -> bool:
        pass

    @abstractmethod
    def shortest_prefix(
        self, key: TrieKey
    ) -> Tuple[Optional[TrieKey], Optional[bytes]]:
        pass

    @abstractmethod
    def longest_prefix(
        self, key: TrieKey
    ) -> Tuple[Optional[TrieKey], Optional[bytes]]:
        pass

    @abstractmethod
    # pylint: disable-next=invalid-name
    def ls(self, key: TrieKey) -> Iterator[TrieKey]:
        pass

    @abstractmethod
    def traverse(
        self, node_factory, prefix: Optional[TrieKey]
    ) -> Iterator[Tuple[TrieKey, bytes]]:
        pass

    @abstractmethod
    def diff(
        self, old: TrieKey, new: TrieKey, with_unchanged: bool = False
    ) -> Iterator[Change]:
        pass
