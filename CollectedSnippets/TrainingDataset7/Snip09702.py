def get_constraints(self, cursor, table_name):
        """
        Retrieve any constraints or keys (unique, pk, fk, check, index) across
        one or more columns.
        """
        constraints = {}
        # Loop over the constraints, getting PKs, uniques, and checks
        cursor.execute(
            """
            SELECT
                user_constraints.constraint_name,
                LISTAGG(LOWER(cols.column_name), ',')
                    WITHIN GROUP (ORDER BY cols.position),
                CASE user_constraints.constraint_type
                    WHEN 'P' THEN 1
                    ELSE 0
                END AS is_primary_key,
                CASE
                    WHEN user_constraints.constraint_type IN ('P', 'U') THEN 1
                    ELSE 0
                END AS is_unique,
                CASE user_constraints.constraint_type
                    WHEN 'C' THEN 1
                    ELSE 0
                END AS is_check_constraint
            FROM
                user_constraints
            LEFT OUTER JOIN
                user_cons_columns cols
                ON user_constraints.constraint_name = cols.constraint_name
            WHERE
                user_constraints.constraint_type = ANY('P', 'U', 'C')
                AND user_constraints.table_name = UPPER(%s)
            GROUP BY user_constraints.constraint_name, user_constraints.constraint_type
            """,
            [table_name],
        )
        for constraint, columns, pk, unique, check in cursor.fetchall():
            constraint = self.identifier_converter(constraint)
            constraints[constraint] = {
                "columns": columns.split(","),
                "primary_key": pk,
                "unique": unique,
                "foreign_key": None,
                "check": check,
                "index": unique,  # All uniques come with an index
            }
        # Foreign key constraints
        cursor.execute(
            """
            SELECT
                cons.constraint_name,
                LISTAGG(LOWER(cols.column_name), ',')
                    WITHIN GROUP (ORDER BY cols.position),
                LOWER(rcols.table_name),
                LOWER(rcols.column_name)
            FROM
                user_constraints cons
            INNER JOIN
                user_cons_columns rcols
                ON rcols.constraint_name = cons.r_constraint_name AND rcols.position = 1
            LEFT OUTER JOIN
                user_cons_columns cols
                ON cons.constraint_name = cols.constraint_name
            WHERE
                cons.constraint_type = 'R' AND
                cons.table_name = UPPER(%s)
            GROUP BY cons.constraint_name, rcols.table_name, rcols.column_name
            """,
            [table_name],
        )
        for constraint, columns, other_table, other_column in cursor.fetchall():
            constraint = self.identifier_converter(constraint)
            constraints[constraint] = {
                "primary_key": False,
                "unique": False,
                "foreign_key": (other_table, other_column),
                "check": False,
                "index": False,
                "columns": columns.split(","),
            }
        # Now get indexes
        cursor.execute(
            """
            SELECT
                ind.index_name,
                LOWER(ind.index_type),
                LOWER(ind.uniqueness),
                LISTAGG(LOWER(cols.column_name), ',')
                    WITHIN GROUP (ORDER BY cols.column_position),
                LISTAGG(cols.descend, ',') WITHIN GROUP (ORDER BY cols.column_position)
            FROM
                user_ind_columns cols, user_indexes ind
            WHERE
                cols.table_name = UPPER(%s) AND
                NOT EXISTS (
                    SELECT 1
                    FROM user_constraints cons
                    WHERE ind.index_name = cons.index_name
                ) AND cols.index_name = ind.index_name
            GROUP BY ind.index_name, ind.index_type, ind.uniqueness
            """,
            [table_name],
        )
        for constraint, type_, unique, columns, orders in cursor.fetchall():
            constraint = self.identifier_converter(constraint)
            constraints[constraint] = {
                "primary_key": False,
                "unique": unique == "unique",
                "foreign_key": None,
                "check": False,
                "index": True,
                "type": "idx" if type_ == "normal" else type_,
                "columns": columns.split(","),
                "orders": orders.split(","),
            }
        return constraints