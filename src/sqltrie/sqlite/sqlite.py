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
ITEMS_SQL = (scripts / "items.sql").read_text()
DIFF_SQL = (scripts / "diff.sql").read_text()


class SQLiteTrie(AbstractTrie):
    def __init__(self, *args, **kwargs):
        self._root_id = ROOT_ID
        self._path = ":memory:"
        super().__init__(*args, **kwargs)

    @classmethod
    def from_path(cls, path):
        trie = cls()
        trie._path = path
        return trie

    @cached_property
    def _conn(self):
        conn = sqlite3.connect(self._path)
        conn.row_factory = sqlite3.Row
        conn.executescript(INIT_SQL)
        return conn

    def _create_node(self, key):
        rows = self._traverse(key, include=["id", "name"])

        pid = rows[-1]["id"] if rows else self._root_id
        for name in key[len(rows) :]:
            row = self._conn.execute(
                """
                INSERT INTO nodes (pid, name) VALUES (?, ?) RETURNING id
                """,
                (pid, name),
            ).fetchone()
            pid = row["id"]

        return pid

    def _traverse(self, key, include=None):
        # FIXME rename to walk_towards or something?

        self._conn.execute("DELETE FROM mysteps")
        self._conn.executemany(
            "INSERT INTO mysteps (depth, name) VALUES (?, ?)",
            ((depth + 1, key[depth]) for depth in range(len(key))),
        )

        rows = self._conn.execute(
            """
            WITH RECURSIVE
                myfunc (id, pid, name, has_value, value, depth) AS (
                    SELECT
                        nodes.id,
                        nodes.pid,
                        nodes.name,
                        nodes.has_value,
                        nodes.value,
                        mysteps.depth
                    FROM nodes, mysteps
                    WHERE
                        mysteps.depth == 1
                        AND nodes.pid == ?
                        AND nodes.name == mysteps.name

                    UNION ALL

                    SELECT
                        nodes.id,
                        nodes.pid,
                        nodes.name,
                        nodes.has_value,
                        nodes.value,
                        myfunc.depth + 1
                    FROM nodes, myfunc, mysteps
                    WHERE
                        nodes.pid == myfunc.id
                        AND mysteps.depth == myfunc.depth + 1
                        AND mysteps.name == nodes.name
                    LIMIT ?
                )
            SELECT id, pid, name, has_value, value FROM myfunc
            """,
            (self._root_id, len(key)),
        ).fetchall()

        return rows

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
        yield from (key for key, _ in self.iteritems())

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
        return self._conn.execute(
            """
            SELECT COUNT(*) AS count FROM nodes WHERE nodes.has_value
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
                [row["name"] for row in rows[: len(rows) - idx]]
            )
            value = row["value"]
            break
        return lkey, value

    def _get_key(self, nid):
        rows = self._conn.execute(
            """
            WITH RECURSIVE
                myfunc (pid, name) AS (
                    SELECT nodes.pid, nodes.name
                    FROM nodes WHERE nodes.id == ?

                    UNION ALL

                    SELECT nodes.pid, nodes.name
                    FROM nodes, myfunc
                    WHERE nodes.id == myfunc.pid AND nodes.id != ?
                )
            SELECT myfunc.name FROM myfunc
            """,
            (nid, self._root_id),
        ).fetchall()

        return tuple(reversed([row["name"] for row in rows]))

    def view(self, key):
        if not key:
            return self

        node = self._get_node(key)

        trie = SQLiteTrie()
        trie._conn = self._conn
        trie._root_id = node["id"]
        return trie

    def items(self, prefix=None, shallow=False):
        if prefix:
            pid = self._get_node(prefix)["id"]
        else:
            prefix = ()
            pid = self._root_id

        self._conn.executescript(ITEMS_SQL.format(root=pid, shallow=shallow))
        rows = self._conn.execute("SELECT * FROM temp_items")

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

    def diff(self, old_key, new_key, with_unchanged=False):
        old_node = self._get_node(old_key)
        new_node = self._get_node(new_key)

        self._conn.executescript(
            DIFF_SQL.format(
                old_root=old_node["id"],
                new_root=new_node["id"],
                with_unchanged=with_unchanged,
            )
        )

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
            for row in self._conn.execute("SELECT * FROM temp_diff")
        )
