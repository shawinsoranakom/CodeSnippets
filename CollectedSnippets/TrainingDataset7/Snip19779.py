def test_database_constraint(self):
        Product.objects.create(price=10, discounted_price=5)
        with self.assertRaises(IntegrityError):
            Product.objects.create(price=10, discounted_price=20)