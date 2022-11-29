"""Tests for `sqltrie` package."""
import pytest

from sqltrie import SQLiteTrie, ShortKeyError

def test_trie():
    trie = SQLiteTrie()

    trie[("foo",)] = "foo-value"
    trie[("foo", "bar", "baz")] = "baz-value"

    assert len(trie) == 2
    assert trie[("foo",)] == "foo-value"
    assert trie[("foo", "bar")] == None
    assert trie[("foo", "bar", "baz")] == "baz-value"

    del trie[("foo",)]
    assert len(trie) == 1
    # FIXME the next two should raise ShortKeyError
    assert trie[("foo",)] == None
    assert trie[("foo", "bar")] == None
    assert trie[("foo", "bar", "baz")] == "baz-value"

    assert set(trie.iteritems()) == set()
