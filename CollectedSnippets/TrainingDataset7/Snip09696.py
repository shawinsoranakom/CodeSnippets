def get_table_list(self, cursor):
        """Return a list of table and view names in the current database."""
        cursor.execute("""
            SELECT
                user_tables.table_name,
                't',
                user_tab_comments.comments
            FROM user_tables
            LEFT OUTER JOIN
                user_tab_comments
                ON user_tab_comments.table_name = user_tables.table_name
            WHERE
                NOT EXISTS (
                    SELECT 1
                    FROM user_mviews
                    WHERE user_mviews.mview_name = user_tables.table_name
                )
            UNION ALL
            SELECT view_name, 'v', NULL FROM user_views
            UNION ALL
            SELECT mview_name, 'v', NULL FROM user_mviews
        """)
        return [
            TableInfo(self.identifier_converter(row[0]), row[1], row[2])
            for row in cursor.fetchall()
        ]