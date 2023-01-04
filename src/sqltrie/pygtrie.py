from pygtrie import Trie as _Trie

from .trie import ADD, DELETE, MODIFY, UNCHANGED, AbstractTrie, Change


class PyGTrie(AbstractTrie):
    def __init__(self, *args, **kwargs):
        self._trie = _Trie()
        super().__init__(*args, **kwargs)

    @classmethod
    def open(cls, path):
        raise NotImplementedError

    def close(self):
        pass

    def commit(self):
        pass

    def rollback(self):
        raise NotImplementedError

    def __setitem__(self, key, value):
        self._trie[key] = value

    def __iter__(self):
        yield from (key for key, _ in self.items())

    def __getitem__(self, key):
        return self._trie[key]

    def __delitem__(self, key):
        del self._trie[key]

    def __len__(self):
        return len(self._trie)

    def has_node(self, key):
        return self._trie.has_node(key)

    def items(self, prefix=None, shallow=False):
        kwargs = {"shallow": shallow}
        if prefix is not None:
            kwargs["prefix"] = prefix

        yield from self._trie.iteritems(**kwargs)

    def prefixes(self, key):
        return self._trie.prefixes(key)

    def shortest_prefix(self, key):
        return self._trie.shortest_prefix(key)

    def longest_prefix(self, key):
        return self._trie.longest_prefix(key)

    def traverse(self, node_factory, prefix=None):
        kwargs = {}
        if prefix is not None:
            kwargs["prefix"] = prefix

        return self._trie.traverse(node_factory, **kwargs)

    def view(self, key=None):
        ret = PyGTrie()
        kwargs = {}
        if key is not None:
            kwargs["prefix"] = key

        for ikey, value in self._trie.iteritems(**kwargs):
            ret[ikey[len(key) :]] = value

        return ret

    def ls(self, key, with_values=False):
        def node_factory(_, nkey, children, *args):
            if nkey == key:
                return children
            return nkey

        return self.traverse(node_factory, prefix=key)

    def diff(self, old, new, with_unchanged=False):
        # FIXME this is not the most optimal implementation
        old_keys = {key for key, _ in self.items(old or ())}
        new_keys = {key for key, _ in self.items(new or ())}

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
            elif not with_unchanged:
                continue

            yield Change(typ, old_entry, new_entry)
