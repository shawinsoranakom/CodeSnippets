def test_lookup_direct_value_rhs_unwrapped(self):
        with self.assertNumQueries(1) as ctx:
            self.assertIs(Author.objects.filter(GreaterThan(2, 1)).exists(), True)
        # Direct values on RHS are not wrapped.
        self.assertIn("2 > 1", ctx.captured_queries[0]["sql"])