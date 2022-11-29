import sqlite3
from functools import cached_property
from .trie import AbstractTrie, ShortKeyError

ROOT_ID = 1

class SQLiteTrie(AbstractTrie):
    def __init__(self, *args, root_id=None, **kwargs):
        self._root_id = root_id or ROOT_ID
#        super().__init__(*args, **kwargs)

    @cached_property
    def _conn(self):
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        conn.executescript(
            """
            CREATE TABLE nodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pid INTEGER,
                name TEXT,
                value TEXT,
                UNIQUE(pid, name)
            );
            CREATE INDEX nodes_pid_idx ON nodes (pid);
            INSERT INTO nodes (id, pid, name, value) VALUES (1, NULL, 'root', NULL)
            """
        )
        return conn

    def _create_node(self, key):
        pid = self._root_id
        for name in key:
            ret = self._conn.execute(
                """
                SELECT id FROM nodes WHERE nodes.pid = ? AND nodes.name = ?
                """,
                (pid, name),
            ).fetchone()
            if ret is None:
                self._conn.execute(
                    """
                    INSERT OR IGNORE INTO nodes (pid, name) VALUES (?, ?)
                    """,
                    (pid, name),
                )
                # FIXME this might not work on IGNORE
                ret = self._conn.execute(
                    "SELECT last_insert_rowid() AS id"
                ).fetchone()
            pid = ret["id"]
        return pid

    def _get_node(self, key):
        if not key:
            return {
                "id": self._root_id,
                "pid": None,
                "name": None,
                "value": None,
            }

        pid = self._root_id
        row = None
        for name in key:
            row = self._conn.execute(
                """
                SELECT id, pid, name, value FROM nodes WHERE nodes.pid = ? AND nodes.name = ?
                """,
                (pid, name),
            ).fetchone()
            if row is None:
                raise KeyError
            pid = row["id"]
        return row

    def _get_children(self, key, limit=None):
        node = self._get_node(key)

        limit_sql = ""
        if limit:
            limit_sql = f"LIMIT {limit}"

        return self._conn.execute(
            f"""
            SELECT * FROM nodes WHERE nodes.pid == ? {limit_sql}
            """,
            (node["id"],)
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
            UPDATE nodes SET value = ? WHERE id = ?
            """,
            (
                value,
                nid,
            )
        )

    def __getitem__(self, key):
        return self._get_node(key)["value"]

    def __delitem__(self, key):
        node = self._get_node(key)
        self._conn.execute(
            f"""
            UPDATE nodes SET value = NULL WHERE id == ?
            """,
            (node["id"],),
        )

    def __len__(self):
        return self._conn.execute(
            """
            SELECT COUNT(*) AS count FROM nodes WHERE nodes.value is not  NULL
            """
        ).fetchone()["count"]

    def iteritems(self, prefix=None, shallow=False):
        assert not shallow
        if prefix:
            pid = self._get_node(prefix)["id"]
        else:
            pid = self._root_id

        cursor = self._conn.execute(
            """
            WITH RECURSIVE
                myfunc (id, pid, name, value) AS (
                    SELECT * FROM nodes WHERE nodes.pid == ?

                    UNION ALL

                    SELECT nodes.id, nodes.pid, nodes.name, nodes.value
                    FROM nodes, myfunc WHERE myfunc.id == nodes.pid
                )
            SELECT * FROM myfunc
            """,
            (pid,)
        )

        for row in cursor:
            # FIXME can join name in the CTE
            yield row

    def clear(self):
        self._conn.execute("DELETE FROM nodes")
