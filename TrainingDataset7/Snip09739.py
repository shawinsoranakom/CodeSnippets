def __foreign_key_constraints(self, table_name, recursive):
        with self.connection.cursor() as cursor:
            if recursive:
                cursor.execute(
                    """
                    SELECT
                        user_tables.table_name, rcons.constraint_name
                    FROM
                        user_tables
                    JOIN
                        user_constraints cons
                        ON (user_tables.table_name = cons.table_name
                        AND cons.constraint_type = ANY('P', 'U'))
                    LEFT JOIN
                        user_constraints rcons
                        ON (user_tables.table_name = rcons.table_name
                        AND rcons.constraint_type = 'R')
                    START WITH user_tables.table_name = UPPER(%s)
                    CONNECT BY
                        NOCYCLE PRIOR cons.constraint_name = rcons.r_constraint_name
                    GROUP BY
                        user_tables.table_name, rcons.constraint_name
                    HAVING user_tables.table_name != UPPER(%s)
                    ORDER BY MAX(level) DESC
                    """,
                    (table_name, table_name),
                )
            else:
                cursor.execute(
                    """
                    SELECT
                        cons.table_name, cons.constraint_name
                    FROM
                        user_constraints cons
                    WHERE
                        cons.constraint_type = 'R'
                        AND cons.table_name = UPPER(%s)
                    """,
                    (table_name,),
                )
            return cursor.fetchall()