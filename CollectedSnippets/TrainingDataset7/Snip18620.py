def test_single_object(self):
        with self.assertNumQueries(1) as ctx:
            Square.objects.bulk_create([Square(root=2, square=4)])
        self.assertNotIn("UNNEST", ctx[0]["sql"])