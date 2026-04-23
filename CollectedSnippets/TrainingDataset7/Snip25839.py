def test_textfield_exact_null(self):
        with self.assertNumQueries(1) as ctx:
            self.assertSequenceEqual(Author.objects.filter(bio=None), [self.au2])
        # Columns with IS NULL condition are not wrapped (except PostgreSQL).
        bio_column = connection.ops.quote_name(Author._meta.get_field("bio").column)
        self.assertIn(f"{bio_column} IS NULL", ctx.captured_queries[0]["sql"])