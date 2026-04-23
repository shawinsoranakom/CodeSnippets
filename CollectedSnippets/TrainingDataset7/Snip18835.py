def test_duplicate_table_error(self):
        """Creating an existing table returns a DatabaseError"""
        query = "CREATE TABLE %s (id INTEGER);" % Article._meta.db_table
        with connection.cursor() as cursor:
            with self.assertRaises(DatabaseError):
                cursor.execute(query)