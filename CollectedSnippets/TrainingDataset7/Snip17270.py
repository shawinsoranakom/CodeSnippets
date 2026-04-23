def _perform_query(self):
        connection = connections[self.database]
        with connection.cursor() as cursor:
            cursor.execute("SELECT 42" + connection.features.bare_select_suffix)
            self.query_results = cursor.fetchall()