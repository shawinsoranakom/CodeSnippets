def test_django_table_names(self):
        with connection.cursor() as cursor:
            cursor.execute("CREATE TABLE django_ixn_test_table (id INTEGER);")
            tl = connection.introspection.django_table_names()
            cursor.execute("DROP TABLE django_ixn_test_table;")
            self.assertNotIn(
                "django_ixn_test_table",
                tl,
                "django_table_names() returned a non-Django table",
            )