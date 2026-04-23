def get_table_description(self, cursor, table_name):
        """
        Return a description of the table with the DB-API cursor.description
        interface.
        """
        # A default collation for the given table/view/materialized view.
        cursor.execute(
            """
            SELECT user_tables.default_collation
            FROM user_tables
            WHERE
                user_tables.table_name = UPPER(%s) AND
                NOT EXISTS (
                    SELECT 1
                    FROM user_mviews
                    WHERE user_mviews.mview_name = user_tables.table_name
                )
            UNION ALL
            SELECT user_views.default_collation
            FROM user_views
            WHERE user_views.view_name = UPPER(%s)
            UNION ALL
            SELECT user_mviews.default_collation
            FROM user_mviews
            WHERE user_mviews.mview_name = UPPER(%s)
            """,
            [table_name, table_name, table_name],
        )
        row = cursor.fetchone()
        default_table_collation = row[0] if row else ""
        # user_tab_columns gives data default for columns
        cursor.execute(
            """
            SELECT
                user_tab_cols.column_name,
                user_tab_cols.data_default,
                CASE
                    WHEN user_tab_cols.collation = %s
                    THEN NULL
                    ELSE user_tab_cols.collation
                END collation,
                CASE
                    WHEN user_tab_cols.char_used IS NULL
                    THEN user_tab_cols.data_length
                    ELSE user_tab_cols.char_length
                END as display_size,
                CASE
                    WHEN user_tab_cols.identity_column = 'YES' THEN 1
                    ELSE 0
                END as is_autofield,
                CASE
                    WHEN EXISTS (
                        SELECT  1
                        FROM user_json_columns
                        WHERE
                            user_json_columns.table_name = user_tab_cols.table_name AND
                            user_json_columns.column_name = user_tab_cols.column_name
                    )
                    THEN 1
                    ELSE 0
                END as is_json,
                user_col_comments.comments as col_comment
            FROM user_tab_cols
            LEFT OUTER JOIN
                user_col_comments ON
                user_col_comments.column_name = user_tab_cols.column_name AND
                user_col_comments.table_name = user_tab_cols.table_name
            WHERE user_tab_cols.table_name = UPPER(%s)
            """,
            [default_table_collation, table_name],
        )
        field_map = {
            column: (
                display_size,
                default.rstrip() if default and default != "NULL" else None,
                collation,
                is_autofield,
                is_json,
                comment,
            )
            for (
                column,
                default,
                collation,
                display_size,
                is_autofield,
                is_json,
                comment,
            ) in cursor.fetchall()
        }
        self.cache_bust_counter += 1
        cursor.execute(
            "SELECT * FROM {} WHERE ROWNUM < 2 AND {} > 0".format(
                self.connection.ops.quote_name(table_name), self.cache_bust_counter
            )
        )
        description = []
        for desc in cursor.description:
            name = desc[0]
            (
                display_size,
                default,
                collation,
                is_autofield,
                is_json,
                comment,
            ) = field_map[name]
            name %= {}  # oracledb, for some reason, doubles percent signs.
            if desc[1] == oracledb.NUMBER and desc[5] == -127 and desc[4] == 0:
                # DecimalField with no precision.
                precision = None
                scale = None
            else:
                precision = desc[4] or 0
                scale = desc[5] or 0
            description.append(
                FieldInfo(
                    self.identifier_converter(name),
                    desc[1],
                    display_size,
                    desc[3],
                    precision,
                    scale,
                    *desc[6:],
                    default,
                    collation,
                    is_autofield,
                    is_json,
                    comment,
                )
            )
        return description