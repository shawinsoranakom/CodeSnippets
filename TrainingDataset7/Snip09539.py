def get_table_list(self, cursor):
        """Return a list of table and view names in the current database."""
        cursor.execute("""
            SELECT
                table_name,
                table_type,
                table_comment
            FROM information_schema.tables
            WHERE table_schema = DATABASE()
            """)
        return [
            TableInfo(row[0], {"BASE TABLE": "t", "VIEW": "v"}.get(row[1]), row[2])
            for row in cursor.fetchall()
        ]