def _perform_query(self):
        with connections[self.database].cursor() as cursor:
            cursor.callproc("test_procedure")
            self.query_results = []