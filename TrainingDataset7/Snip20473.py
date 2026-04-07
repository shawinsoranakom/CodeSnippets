def test_float(self):
        FloatModel.objects.create(f1=-0.5, f2=0.87)
        obj = FloatModel.objects.annotate(
            f1_asin=ASin("f1"), f2_asin=ASin("f2")
        ).first()
        self.assertIsInstance(obj.f1_asin, float)
        self.assertIsInstance(obj.f2_asin, float)
        self.assertAlmostEqual(obj.f1_asin, math.asin(obj.f1))
        self.assertAlmostEqual(obj.f2_asin, math.asin(obj.f2))