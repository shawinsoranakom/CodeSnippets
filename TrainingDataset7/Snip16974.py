def test_avg_decimal_field(self):
        v = Book.objects.filter(rating=4).aggregate(avg_price=(Avg("price")))[
            "avg_price"
        ]
        self.assertIsInstance(v, Decimal)
        self.assertEqual(v, Approximate(Decimal("47.39"), places=2))