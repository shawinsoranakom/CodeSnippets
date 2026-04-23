def get_storage_engine(self, cursor, table_name):
        """
        Retrieve the storage engine for a given table. Return the default
        storage engine if the table doesn't exist.
        """
        cursor.execute(
            """
            SELECT engine
            FROM information_schema.tables
            WHERE
                table_name = %s AND
                table_schema = DATABASE()
            """,
            [table_name],
        )
        result = cursor.fetchone()
        if not result:
            return self.connection.features._mysql_storage_engine
        return result[0]