def _get_table_comment(self, table, using):
        with connections[using].cursor() as cursor:
            return next(
                t.comment
                for t in connections[using].introspection.get_table_list(cursor)
                if t.name == table
            )