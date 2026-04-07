def test_sql_generation_idempotency(self):
        qs = Article.objects.annotate(description=Concat("title", V(": "), "summary"))
        # Multiple compilations should not alter the generated query.
        self.assertEqual(str(qs.query), str(qs.all().query))