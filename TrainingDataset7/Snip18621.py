def test_non_literal(self):
        with self.assertNumQueries(1) as ctx:
            Square.objects.bulk_create(
                [Square(root=2, square=RawSQL("%s", (4,))), Square(root=3, square=9)]
            )
        self.assertNotIn("UNNEST", ctx[0]["sql"])