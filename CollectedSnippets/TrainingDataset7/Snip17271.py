def _perform_query(self):
        from ..models import TotallyNormal

        connection = connections[self.database]
        table_meta = TotallyNormal._meta
        with connection.cursor() as cursor:
            cursor.executemany(
                "INSERT INTO %s (%s) VALUES(%%s)"
                % (
                    connection.introspection.identifier_converter(table_meta.db_table),
                    connection.ops.quote_name(table_meta.get_field("name").column),
                ),
                [("test name 1",), ("test name 2",)],
            )
            self.query_results = []