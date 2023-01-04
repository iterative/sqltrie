import pytest

from sqltrie import PyGTrie, SQLiteTrie

NFILES = 10000
NSUBDIRS = 3


@pytest.fixture(scope="session")
def items():
    ret = {}

    files = {str(idx): bytes(idx) for idx in range(NFILES)}
    for subdir in range(NSUBDIRS):
        ret[str(subdir)] = files.copy()

    return ret


@pytest.mark.parametrize("cls", [SQLiteTrie, PyGTrie])
def test_set(benchmark, items, cls):
    def _set():
        trie = cls()

        for subdir in range(NSUBDIRS):
            for idx in range(NFILES):
                trie[(str(subdir), str(idx))] = bytes(idx)

    benchmark(_set)


@pytest.mark.parametrize("cls", [SQLiteTrie, PyGTrie])
def test_items(benchmark, items, cls):
    trie = cls()

    for subdir in range(NSUBDIRS):
        for idx in range(NFILES):
            trie[(str(subdir), str(idx))] = bytes(idx)

    def _items():
        list(trie.items())

    benchmark(_items)


@pytest.mark.parametrize("cls", [SQLiteTrie, PyGTrie])
def test_ls(benchmark, items, cls):
    trie = cls()

    for subdir in range(NSUBDIRS):
        for idx in range(NFILES):
            trie[(str(subdir), str(idx))] = bytes(idx)

    def _ls():
        list(trie.ls(("1",)))

    benchmark(_ls)


@pytest.mark.parametrize("cls", [SQLiteTrie, PyGTrie])
def test_diff(benchmark, items, cls):
    trie = cls()

    for subdir in range(NSUBDIRS):
        for idx in range(NFILES):
            trie[(str(subdir), str(idx))] = bytes(idx)

    def _diff():
        list(trie.diff(None, None))

    benchmark(_diff)
