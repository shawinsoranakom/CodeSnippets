def test_fast_delete_all(self):
        with self.assertNumQueries(1) as ctx:
            User.objects.all().delete()
        sql = ctx.captured_queries[0]["sql"]
        # No subqueries is used when performing a full delete.
        self.assertNotIn("SELECT", sql)