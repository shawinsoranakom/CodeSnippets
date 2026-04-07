def get_constraints(self, cursor, table_name):
        """
        Retrieve any constraints or keys (unique, pk, fk, check, index) across
        one or more columns. Also retrieve the definition of expression-based
        indexes.
        """
        constraints = {}
        # Loop over the key table, collecting things as constraints. The column
        # array must return column names in the same order in which they were
        # created.
        cursor.execute(
            """
            SELECT
                c.conname,
                array(
                    SELECT attname
                    FROM unnest(c.conkey) WITH ORDINALITY cols(colid, arridx)
                    JOIN pg_attribute AS ca ON cols.colid = ca.attnum
                    WHERE ca.attrelid = c.conrelid
                    ORDER BY cols.arridx
                ),
                c.contype,
                (SELECT fkc.relname || '.' || fka.attname
                FROM pg_attribute AS fka
                JOIN pg_class AS fkc ON fka.attrelid = fkc.oid
                WHERE fka.attrelid = c.confrelid AND fka.attnum = c.confkey[1]),
                cl.reloptions
            FROM pg_constraint AS c
            JOIN pg_class AS cl ON c.conrelid = cl.oid
            WHERE cl.relname = %s
                AND pg_catalog.pg_table_is_visible(cl.oid)
                AND c.contype != 'n'
        """,
            [table_name],
        )
        for constraint, columns, kind, used_cols, options in cursor.fetchall():
            constraints[constraint] = {
                "columns": columns,
                "primary_key": kind == "p",
                "unique": kind in ["p", "u"],
                "foreign_key": tuple(used_cols.split(".", 1)) if kind == "f" else None,
                "check": kind == "c",
                "index": False,
                "definition": None,
                "options": options,
            }
        # Now get indexes
        cursor.execute(
            """
            SELECT
                indexname,
                array_agg(attname ORDER BY arridx),
                indisunique,
                indisprimary,
                array_agg(ordering ORDER BY arridx),
                amname,
                exprdef,
                s2.attoptions
            FROM (
                SELECT
                    c2.relname as indexname, idx.*, attr.attname, am.amname,
                    CASE
                        WHEN idx.indexprs IS NOT NULL THEN
                            pg_get_indexdef(idx.indexrelid)
                    END AS exprdef,
                    CASE am.amname
                        WHEN %s THEN
                            CASE (option & 1)
                                WHEN 1 THEN 'DESC' ELSE 'ASC'
                            END
                    END as ordering,
                    c2.reloptions as attoptions
                FROM (
                    SELECT *
                    FROM
                        pg_index i,
                        unnest(i.indkey, i.indoption)
                            WITH ORDINALITY koi(key, option, arridx)
                ) idx
                LEFT JOIN pg_class c ON idx.indrelid = c.oid
                LEFT JOIN pg_class c2 ON idx.indexrelid = c2.oid
                LEFT JOIN pg_am am ON c2.relam = am.oid
                LEFT JOIN
                    pg_attribute attr ON attr.attrelid = c.oid AND attr.attnum = idx.key
                WHERE c.relname = %s AND pg_catalog.pg_table_is_visible(c.oid)
            ) s2
            GROUP BY indexname, indisunique, indisprimary, amname, exprdef, attoptions;
        """,
            [self.index_default_access_method, table_name],
        )
        for (
            index,
            columns,
            unique,
            primary,
            orders,
            type_,
            definition,
            options,
        ) in cursor.fetchall():
            if index not in constraints:
                basic_index = (
                    type_ == self.index_default_access_method
                    and
                    # '_btree' references
                    # django.contrib.postgres.indexes.BTreeIndex.suffix.
                    not index.endswith("_btree")
                    and options is None
                )
                constraints[index] = {
                    "columns": columns if columns != [None] else [],
                    "orders": orders if orders != [None] else [],
                    "primary_key": primary,
                    "unique": unique,
                    "foreign_key": None,
                    "check": False,
                    "index": True,
                    "type": Index.suffix if basic_index else type_,
                    "definition": definition,
                    "options": options,
                }
        return constraints