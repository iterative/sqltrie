import pytest
from pygtrie import Trie as _GTrie

from sqltrie import ADD, DELETE, MODIFY, UNCHANGED, Change, SQLiteTrie

NFILES = 10000
NSUBDIRS = 3


class GTrie(_GTrie):
    def ls(self, root_key):
        def node_factory(_, key, children, *args):
            if key == root_key:
                return children
            else:
                return key

        return self.traverse(node_factory, prefix=root_key)

    def diff(self, old, new):
        # FIXME this is not the most optimal implementation
        old_keys = {key for key, _ in self.iteritems(old or ())}
        new_keys = {key for key, _ in self.iteritems(new or ())}

        for key in old_keys | new_keys:
            old_entry = self.get(key)
            new_entry = self.get(key)

            typ = UNCHANGED
            if old_entry and not new_entry:
                typ = DELETE
            elif not old_entry and new_entry:
                typ = ADD
            elif old_entry != new_entry:
                typ = MODIFY
            else:
                continue

            yield Change(typ, old_entry, new_entry)


@pytest.fixture(scope="session")
def items():
    ret = {}

    files = {str(idx): bytes(idx) for idx in range(NFILES)}
    for subdir in range(NSUBDIRS):
        ret[str(subdir)] = files.copy()

    return ret


@pytest.mark.parametrize("cls", [SQLiteTrie, GTrie])
def test_set(benchmark, items, cls):
    def _set():
        trie = cls()

        for subdir in range(NSUBDIRS):
            for idx in range(NFILES):
                trie[(str(subdir), str(idx))] = bytes(idx)

    benchmark(_set)


@pytest.mark.parametrize("cls", [SQLiteTrie, GTrie])
def test_items(benchmark, items, cls):
    trie = cls()

    for subdir in range(NSUBDIRS):
        for idx in range(NFILES):
            trie[(str(subdir), str(idx))] = bytes(idx)

    def _items():
        list(trie.items())

    benchmark(_items)


@pytest.mark.parametrize("cls", [SQLiteTrie, GTrie])
def test_ls(benchmark, items, cls):
    trie = cls()

    for subdir in range(NSUBDIRS):
        for idx in range(NFILES):
            trie[(str(subdir), str(idx))] = bytes(idx)

    def _ls():
        list(trie.ls(("1",)))

    benchmark(_ls)


@pytest.mark.parametrize("cls", [SQLiteTrie, GTrie])
def test_diff(benchmark, items, cls):
    trie = cls()

    for subdir in range(NSUBDIRS):
        for idx in range(NFILES):
            trie[(str(subdir), str(idx))] = bytes(idx)

    def _diff():
        list(trie.diff(None, None))

    benchmark(_diff)
