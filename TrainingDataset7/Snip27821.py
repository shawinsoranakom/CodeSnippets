def test_default(self):
        f = models.DecimalField(default=Decimal("0.00"))
        self.assertEqual(f.get_default(), Decimal("0.00"))