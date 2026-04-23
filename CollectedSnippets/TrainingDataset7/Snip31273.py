def get_table_comment(self, table):
        with connection.cursor() as cursor:
            return next(
                t.comment
                for t in connection.introspection.get_table_list(cursor)
                if t.name == table
            )