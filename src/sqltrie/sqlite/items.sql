DROP TABLE IF EXISTS temp_items;

CREATE TEMP TABLE temp_items AS
WITH RECURSIVE children (
    id, pid, name, path, has_value, value, found_value
) AS (
    SELECT
        nodes.id,
        nodes.pid,
        nodes.name,
        nodes.name,
        nodes.has_value,
        nodes.value,
        nodes.has_value
    FROM nodes WHERE nodes.pid == {root}

    UNION ALL

    SELECT
        nodes.id,
        nodes.pid,
        nodes.name,
        children.path || '/' || nodes.name,
        nodes.has_value,
        nodes.value,
        children.found_value OR nodes.has_value
    FROM nodes, children
    WHERE children.id == nodes.pid AND (NOT {shallow} OR NOT children.found_value OR nodes.has_value)
)

SELECT
    id,
    pid,
    name,
    path,
    has_value,
    value
FROM children WHERE has_value;
