def test_decimal(self):
        DecimalModel.objects.create(n1=Decimal("-12.9"), n2=Decimal("0.6"))
        obj = DecimalModel.objects.annotate(
            n1_floor=Floor("n1"), n2_floor=Floor("n2")
        ).first()
        self.assertIsInstance(obj.n1_floor, Decimal)
        self.assertIsInstance(obj.n2_floor, Decimal)
        self.assertEqual(obj.n1_floor, Decimal(math.floor(obj.n1)))
        self.assertEqual(obj.n2_floor, Decimal(math.floor(obj.n2)))