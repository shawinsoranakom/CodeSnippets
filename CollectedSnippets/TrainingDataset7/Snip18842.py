def test_queries_bare_where(self):
        sql = f"SELECT 1{connection.features.bare_select_suffix} WHERE 1=1"
        with connection.cursor() as cursor:
            cursor.execute(sql)
            self.assertEqual(cursor.fetchone(), (1,))