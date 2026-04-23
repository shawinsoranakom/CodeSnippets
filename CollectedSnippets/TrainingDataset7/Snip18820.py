def test_paramless_no_escaping(self):
        with connection.cursor() as cursor:
            cursor.execute("SELECT '%s'" + self.bare_select_suffix)
            self.assertEqual(cursor.fetchall()[0][0], "%s")