def test_count_star(self):
        with self.assertNumQueries(1) as ctx:
            Book.objects.aggregate(n=Count("*"))
        sql = ctx.captured_queries[0]["sql"]
        self.assertIn("SELECT COUNT(*) ", sql)