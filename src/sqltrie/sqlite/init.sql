CREATE TABLE nodes (
    id integer PRIMARY KEY AUTOINCREMENT,
    pid integer,
    name text,
    has_value boolean,
    value blob,
    UNIQUE(pid, name)
);
CREATE INDEX nodes_pid_idx ON nodes (pid);
INSERT INTO nodes (id, pid, name, has_value, value)
VALUES (1, NULL, "", FALSE, NULL);

CREATE TEMP TABLE mysteps (depth integer PRIMARY KEY, name text NOT NULL);
