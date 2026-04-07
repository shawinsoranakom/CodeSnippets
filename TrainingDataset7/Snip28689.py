def test_create_child_no_update(self):
        """Creating a child with non-abstract parents only issues INSERTs."""

        def a():
            GrandChild.objects.create(
                email="grand_parent@example.com",
                first_name="grand",
                last_name="parent",
            )

        def b():
            GrandChild().save()

        for i, test in enumerate([a, b]):
            with (
                self.subTest(i=i),
                self.assertNumQueries(4),
                CaptureQueriesContext(connection) as queries,
            ):
                test()
                for query in queries:
                    sql = query["sql"]
                    self.assertIn("INSERT INTO", sql, sql)