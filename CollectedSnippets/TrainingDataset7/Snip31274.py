def assert_column_comment_not_exists(self, table, column):
        with connection.cursor() as cursor:
            columns = connection.introspection.get_table_description(cursor, table)
        self.assertFalse(any([c.name == column and c.comment for c in columns]))