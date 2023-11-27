import pytest

from sqltrie import PyGTrie, SQLiteTrie


@pytest.fixture(scope="session")
def tree():
    ret = {}

    # NOTE: emulating mnist dataset from dvc-bench
    # TODO: ability to test multiple mockup datasets, maybe even with a CLI flag

    ret["train"] = None
    for subdir_idx in range(10):
        subdir_key = ("train", str(subdir_idx))
        ret[subdir_key] = None
        for file_idx in range(1100):
            file_key = (*subdir_key, str(file_idx))
            ret[file_key] = bytes(file_idx)

    ret["test"] = None
    for subdir_idx in range(10):
        subdir_key = ("test", str(subdir_idx))
        ret[subdir_key] = None
        for file_idx in range(6000):
            file_key = (*subdir_key, str(file_idx))
            ret[file_key] = bytes(file_idx)

    return ret


@pytest.fixture
def make_trie(tree):
    def _make_trie(cls):
        trie = cls()

        for key, value in tree.items():
            trie[key] = value

        return trie

    return _make_trie


@pytest.mark.parametrize("cls", [SQLiteTrie, PyGTrie])
def test_set(benchmark, tree, cls):
    trie = cls()

    def _set():
        for key, value in tree.items():
            trie[key] = value

    benchmark(_set)


@pytest.mark.parametrize("cls", [SQLiteTrie, PyGTrie])
def test_items(benchmark, make_trie, cls):
    trie = make_trie(cls)

    def _items():
        list(trie.items())

    benchmark(_items)


@pytest.mark.parametrize("cls", [SQLiteTrie, PyGTrie])
def test_len(benchmark, make_trie, cls):
    trie = make_trie(cls)

    def _len():
        len(trie)

    benchmark(_len)


@pytest.mark.parametrize("cls", [SQLiteTrie, PyGTrie])
def test_traverse(benchmark, make_trie, cls):
    trie = make_trie(cls)

    def traverse():
        def node_factory(path_conv, key, children, *args):
            list(children)

        trie.traverse(node_factory)

    benchmark(traverse)


@pytest.mark.parametrize("cls", [SQLiteTrie, PyGTrie])
def test_ls(benchmark, make_trie, cls):
    trie = make_trie(cls)

    def _ls():
        list(trie.ls(()))

    benchmark(_ls)


@pytest.mark.parametrize("cls", [SQLiteTrie, PyGTrie])
def test_diff(benchmark, make_trie, cls):
    trie = make_trie(cls)

    def _diff():
        list(trie.diff(None, None))

    benchmark(_diff)
