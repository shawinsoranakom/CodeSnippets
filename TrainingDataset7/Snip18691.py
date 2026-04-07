def test_copy_to_expert_cursors(self):
        out = StringIO()
        copy_expert_sql = "COPY django_session TO STDOUT (FORMAT CSV, HEADER)"
        with connection.cursor() as cursor:
            cursor.copy_expert(copy_expert_sql, out)
            cursor.copy_to(out, "django_session")
        self.assertEqual(
            [q["sql"] for q in connection.queries],
            [copy_expert_sql, "COPY django_session TO STDOUT"],
        )