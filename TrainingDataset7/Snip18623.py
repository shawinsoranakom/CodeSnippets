def test_unnest_eligible_db_default(self):
        with self.assertNumQueries(1) as ctx:
            squares = Square.objects.bulk_create([Square(root=3), Square(root=3)])
        self.assertIn("UNNEST", ctx[0]["sql"])
        self.assertEqual([square.square for square in squares], [9, 9])