def test_unnest_eligible(self):
        with self.assertNumQueries(1) as ctx:
            Square.objects.bulk_create(
                [Square(root=2, square=4), Square(root=3, square=9)]
            )
        self.assertIn("UNNEST", ctx[0]["sql"])