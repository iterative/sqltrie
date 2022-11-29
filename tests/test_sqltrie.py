"""Tests for `sqltrie` package."""
import pytest

from sqltrie import UNCHANGED, Change, ShortKeyError, SQLiteTrie, TrieNode


def test_trie():
    trie = SQLiteTrie()

    trie[("foo",)] = b"foo-value"
    trie[("foo", "bar", "baz")] = b"baz-value"

    assert len(trie) == 2
    assert trie[("foo",)] == b"foo-value"
    with pytest.raises(ShortKeyError):
        trie[("foo", "bar")]  # pylint: disable=pointless-statement
    assert trie[("foo", "bar", "baz")] == b"baz-value"

    del trie[("foo",)]
    assert len(trie) == 1
    assert trie[("foo", "bar", "baz")] == b"baz-value"

    with pytest.raises(ShortKeyError):
        trie[("foo",)]  # pylint: disable=pointless-statement

    with pytest.raises(ShortKeyError):
        trie[("foo", "bar")]  # pylint: disable=pointless-statement

    with pytest.raises(KeyError):
        trie[("non-existent",)]  # pylint: disable=pointless-statement

    with pytest.raises(KeyError):
        trie[("foo", "non-existent")]  # pylint: disable=pointless-statement

    assert trie.longest_prefix(("non-existent",)) == ((), None)
    assert trie.longest_prefix(("foo",)) == ((), None)
    assert trie.longest_prefix(("foo", "non-existent")) == ((), None)
    assert trie.longest_prefix(("foo", "bar", "baz", "qux")) == (
        ("foo", "bar", "baz"),
        b"baz-value",
    )

    assert set(trie.items()) == {
        (("foo", "bar", "baz"), b"baz-value"),
    }
    assert set(trie.items(shallow=True)) == {
        (("foo", "bar", "baz"), b"baz-value"),
    }
    assert set(trie.items(("foo",))) == {
        (("foo", "bar", "baz"), b"baz-value"),
    }
    assert set(trie.items(("foo", "bar"))) == {
        (("foo", "bar", "baz"), b"baz-value"),
    }
    assert set(trie.items(("foo", "bar", "baz"))) == set()

    assert set(trie.view(("foo", "bar", "baz")).items()) == set()

    assert list(trie.ls(())) == [("foo",)]
    assert list(trie.ls(("foo",))) == [("foo", "bar")]
    assert list(trie.ls(("foo", "bar"))) == [("foo", "bar", "baz")]

    assert not list(trie.diff(("foo",), ("foo",)))
    assert list(trie.diff(("foo",), ("foo",), with_unchanged=True)) == [
        Change(
            typ=UNCHANGED,
            old=TrieNode(key=("bar",), value=None),
            new=TrieNode(key=("bar",), value=None),
        ),
        Change(
            typ=UNCHANGED,
            old=TrieNode(key=("bar", "baz"), value=b"baz-value"),
            new=TrieNode(key=("bar", "baz"), value=b"baz-value"),
        ),
    ]
