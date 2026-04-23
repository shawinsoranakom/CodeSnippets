def test_order_of_precedence(self):
        p1 = Book.objects.filter(rating=4).aggregate(avg_price=(Avg("price") + 2) * 3)
        self.assertEqual(p1, {"avg_price": Approximate(Decimal("148.18"), places=2)})

        p2 = Book.objects.filter(rating=4).aggregate(avg_price=Avg("price") + 2 * 3)
        self.assertEqual(p2, {"avg_price": Approximate(Decimal("53.39"), places=2)})