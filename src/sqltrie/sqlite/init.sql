CREATE TABLE IF NOT EXISTS nodes (
    id integer PRIMARY KEY AUTOINCREMENT,
    pid integer,
    name text,
    has_value boolean,
    value blob,
    UNIQUE(pid, name),
    UNIQUE(id, pid),
    CHECK(id != pid)
);
CREATE INDEX IF NOT EXISTS nodes_pid_idx ON nodes (pid);
INSERT OR IGNORE INTO nodes (id, pid, name, has_value, value)
VALUES (1, NULL, "", FALSE, NULL);
