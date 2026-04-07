def test_parameter_escaping(self):
        with connection.cursor() as cursor:
            cursor.execute("SELECT '%%', %s" + self.bare_select_suffix, ("%d",))
            self.assertEqual(cursor.fetchall()[0], ("%", "%d"))