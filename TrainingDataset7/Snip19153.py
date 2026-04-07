def drop_table(self):
        with connection.cursor() as cursor:
            table_name = connection.ops.quote_name("test cache table")
            cursor.execute("DROP TABLE %s" % table_name)