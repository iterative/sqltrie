import sqlite3
from functools import cached_property
from pathlib import Path
from typing import Iterator, Optional, Tuple

from ..trie import AbstractTrie, Change, ShortKeyError, TrieKey, TrieNode

# NOTE: seems like "named" doesn't work without changing this global var,
# so unfortunately we have to stick with qmark.
assert sqlite3.paramstyle == "qmark"

scripts = Path(__file__).parent

ROOT_ID = 1
ROOT_NAME = "/"

INIT_SQL = (scripts / "init.sql").read_text()

STEPS_SQL = (scripts / "steps.sql").read_text()
STEPS_TABLE = "temp_steps"

ITEMS_SQL = (scripts / "items.sql").read_text()
ITEMS_TABLE = "temp_items"

DIFF_SQL = (scripts / "diff.sql").read_text()
DIFF_TABLE = "temp_diff"


class SQLiteTrie(AbstractTrie):
    def __init__(self, *args, **kwargs):
        self._root_id = ROOT_ID
        self._path = ":memory:"
        self._ids = {}
        super().__init__(*args, **kwargs)

    @classmethod
    def from_path(cls, path):
        trie = cls()
        trie._path = path
        return trie

    @cached_property
    def _conn(self):  # pylint: disable=method-hidden
        conn = sqlite3.connect(self._path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.executescript(INIT_SQL)
        return conn

    def _create_node(self, key):
        try:
            return self._ids[key]
        except KeyError:
            pass

        parent = key[:-1]
        try:
            pid = self._ids[parent]
            longest_prefix = parent
        except KeyError:
            rows = self._traverse(key)
            if rows:
                longest_prefix = tuple(rows[-1]["path"].split("/"))
                pid = rows[-1]["id"]
            else:
                longest_prefix = ()
                pid = self._root_id
            self._ids[longest_prefix] = pid

        node_key = longest_prefix
        for name in key[len(longest_prefix) :]:
            node_key = (*node_key, name)
            row = self._conn.execute(
                """
                INSERT INTO nodes (pid, name) VALUES (?, ?) RETURNING id
                """,
                (pid, name),
            ).fetchone()
            nid = row["id"]
            self._ids[node_key] = nid
            pid = nid

        return pid

    def _traverse(self, key):
        self._conn.executescript(
            STEPS_SQL.format(path="/".join(key), root=self._root_id)
        )

        return self._conn.execute(  # nosec
            f"SELECT * FROM {STEPS_TABLE}"
        ).fetchall()

    def _get_node(self, key):
        if not key:
            return {
                "id": self._root_id,
                "pid": None,
                "name": None,
                "value": None,
            }

        rows = list(self._traverse(key))
        if len(rows) != len(key):
            raise KeyError(key)

        return rows[-1]

    def _get_children(self, key, limit=None):
        node = self._get_node(key)

        limit_sql = ""
        if limit:
            limit_sql = f"LIMIT {limit}"

        return self._conn.execute(  # nosec
            f"""
            SELECT * FROM nodes WHERE nodes.pid == ? {limit_sql}
            """,
            (node["id"],),
        ).fetchall()

    def _delete_node(self, key):
        node = self._get_node(key)
        del self._ids[key]
        self._conn.execute(
            """
            DELETE FROM nodes WHERE id = ?
            """,
            (node["id"],),
        )

    def __setitem__(self, key, value):
        nid = self._create_node(key)
        self._conn.execute(
            """
            UPDATE nodes SET has_value = True, value = ? WHERE id = ?
            """,
            (
                value,
                nid,
            ),
        )

    def __iter__(self):
        yield from (key for key, _ in self.items())

    def __getitem__(self, key):
        value = self._get_node(key)["value"]
        if not value:
            raise ShortKeyError(key)
        return value

    def __delitem__(self, key):
        node = self._get_node(key)
        self._conn.execute(
            """
            UPDATE nodes SET has_value = False, value = NULL WHERE id == ?
            """,
            (node["id"],),
        )

    def __len__(self):
        self._conn.executescript(
            ITEMS_SQL.format(root=self._root_id, shallow=False)
        )
        return self._conn.execute(  # nosec
            f"""
            SELECT COUNT(*) AS count FROM {ITEMS_TABLE}
            """
        ).fetchone()["count"]

    def shortest_prefix(
        self, key: TrieKey
    ) -> Tuple[Optional[TrieKey], Optional[bytes]]:
        skey: TrieKey = ()
        value = None
        for row in self._traverse(key):
            skey = (*skey, row["name"])  # type: ignore
            value = row["value"]
            if value is not None:
                break

        return skey, value

    def longest_prefix(self, key) -> Tuple[Optional[TrieKey], Optional[bytes]]:
        rows = self._traverse(key)
        lkey: TrieKey = ()
        value = None
        for idx, row in enumerate(reversed(rows)):
            if row["value"] is None:
                continue
            lkey = tuple(  # type: ignore
                row["name"] for row in rows[: len(rows) - idx]
            )
            value = row["value"]
            break
        return lkey, value

    def view(  # type: ignore
        self,
        key: Optional[TrieKey] = None,
    ) -> "SQLiteTrie":
        if not key:
            return self

        node = self._get_node(key)

        trie = SQLiteTrie()
        trie._conn = self._conn  # pylint: disable=protected-access
        trie._root_id = node["id"]  # pylint: disable=protected-access
        return trie

    def items(self, prefix=None, shallow=False):
        if prefix:
            pid = self._get_node(prefix)["id"]
        else:
            prefix = ()
            pid = self._root_id

        self._conn.executescript(ITEMS_SQL.format(root=pid, shallow=shallow))
        rows = self._conn.execute(f"SELECT * FROM {ITEMS_TABLE}")  # nosec

        yield from (
            ((*prefix, *row["path"].split("/")), row["value"]) for row in rows
        )

    def clear(self):
        self._conn.execute("DELETE FROM nodes")

    def has_node(self, key: TrieKey) -> bool:
        try:
            value = self[key]
            return value is not None
        except KeyError:
            return False

    def ls(self, key: TrieKey) -> Iterator[TrieKey]:
        yield from (  # type: ignore
            (*key, row["name"]) for row in self._get_children(key)
        )

    def traverse(self, node_factory, prefix=None):
        key = prefix or ()
        row = self._get_node(prefix)
        value = row["value"]

        children_keys = (
            (*key, row["name"]) for row in self._get_children(key)
        )
        children = (
            self.traverse(node_factory, child) for child in children_keys
        )

        return node_factory(None, key, children, value)

    def diff(self, old, new, with_unchanged=False):
        old_node = self._get_node(old)
        new_node = self._get_node(new)

        self._conn.executescript(
            DIFF_SQL.format(
                old_root=old_node["id"],
                new_root=new_node["id"],
                with_unchanged=with_unchanged,
            )
        )

        rows = self._conn.execute(f"SELECT * FROM {DIFF_TABLE}")  # nosec
        yield from (
            Change(
                row["type"],
                TrieNode(
                    tuple(row["old_path"].split("/")),
                    row["old_value"],
                ),
                TrieNode(
                    tuple(row["new_path"].split("/")),
                    row["new_value"],
                ),
            )
            for row in rows
        )
