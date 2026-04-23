def test_nested_queries_sql(self):
        # Nested queries should not evaluate the inner query as part of
        # constructing the SQL (so we should see a nested query here, indicated
        # by two "SELECT" calls).
        qs = Annotation.objects.filter(notes__in=Note.objects.filter(note="xyzzy"))
        self.assertEqual(qs.query.get_compiler(qs.db).as_sql()[0].count("SELECT"), 2)