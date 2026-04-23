def test_parameter_quoting(self):
        # The implementation of last_executed_queries isn't optimal. It's
        # worth testing that parameters are quoted (#14091).
        query = "SELECT %s"
        params = ["\"'\\"]
        with connection.cursor() as cursor:
            cursor.execute(query, params)
        # Note that the single quote is repeated
        substituted = "SELECT '\"''\\'"
        self.assertEqual(connection.queries[-1]["sql"], substituted)