def get_column_comment(self, table, column):
        with connection.cursor() as cursor:
            return next(
                f.comment
                for f in connection.introspection.get_table_description(cursor, table)
                if f.name == column
            )