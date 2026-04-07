def test_parameter_escaping(self):
        # '%s' escaping support for sqlite3 (#13648).
        with connection.cursor() as cursor:
            cursor.execute("select strftime('%s', date('now'))")
            response = cursor.fetchall()[0][0]
        # response should be an non-zero integer
        self.assertTrue(int(response))