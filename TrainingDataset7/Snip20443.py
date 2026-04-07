def test_explicit_cast(self):
        qs = Author.objects.annotate(
            json_array=JSONArray(Cast("age", CharField()))
        ).values("json_array")
        with self.assertNumQueries(1) as ctx:
            self.assertSequenceEqual(qs, [{"json_array": ["30"]}])
        sql = ctx.captured_queries[0]["sql"]
        self.assertIn("::varchar", sql)
        self.assertNotIn("::varchar)::varchar", sql)