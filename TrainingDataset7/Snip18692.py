def test_copy_cursors(self):
        copy_sql = "COPY django_session TO STDOUT (FORMAT CSV, HEADER)"
        with connection.cursor() as cursor:
            with cursor.copy(copy_sql) as copy:
                for row in copy:
                    pass
        self.assertEqual([q["sql"] for q in connection.queries], [copy_sql])