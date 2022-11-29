import pytest

from sqltrie import SQLiteTrie


@pytest.fixture(scope="session")
def items():
    ret = {}

    files = {str(idx): bytes(idx) for idx in range(10000)}
    for subdir in ["foo", "bar", "baz"]:
        ret[subdir] = files.copy()

    return ret


def test_set(benchmark, items):
    def _set():
        trie = SQLiteTrie()

        for subdir in ["foo", "bar", "baz"]:
            for idx in range(10000):
                trie[(subdir, str(idx))] = bytes(idx)

    benchmark(_set)


def test_items(benchmark, items):
    trie = SQLiteTrie()

    for subdir in ["foo", "bar", "baz"]:
        for idx in range(10000):
            trie[(subdir, str(idx))] = bytes(idx)

    def _items():
        list(trie.items())

    benchmark(_items)
