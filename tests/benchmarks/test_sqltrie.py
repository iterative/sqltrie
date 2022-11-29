import pytest
from pygtrie import Trie as GTrie

from sqltrie import SQLiteTrie


@pytest.fixture(scope="session")
def items():
    ret = {}

    files = {str(idx): bytes(idx) for idx in range(10000)}
    for subdir in ["foo", "bar", "baz"]:
        ret[subdir] = files.copy()

    return ret


@pytest.mark.parametrize("cls", [SQLiteTrie, GTrie])
def test_set(benchmark, items, cls):
    def _set():
        trie = cls()

        for subdir in ["foo", "bar", "baz"]:
            for idx in range(10000):
                trie[(subdir, str(idx))] = bytes(idx)

    benchmark(_set)


@pytest.mark.parametrize("cls", [SQLiteTrie, GTrie])
def test_items(benchmark, items, cls):
    trie = SQLiteTrie()

    for subdir in ["foo", "bar", "baz"]:
        for idx in range(10000):
            trie[(subdir, str(idx))] = bytes(idx)

    def _items():
        list(trie.items())

    benchmark(_items)


def test_diff(benchmark, items):
    trie = SQLiteTrie()

    for subdir in ["foo", "bar", "baz"]:
        for idx in range(10000):
            trie[(subdir, str(idx))] = bytes(idx)

    def _diff():
        list(trie.diff(None, None))

    benchmark(_diff)
