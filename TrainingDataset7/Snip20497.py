def test_float(self):
        FloatModel.objects.create(f1=-27.5, f2=0.33)
        obj = FloatModel.objects.annotate(f1_cot=Cot("f1"), f2_cot=Cot("f2")).first()
        self.assertIsInstance(obj.f1_cot, float)
        self.assertIsInstance(obj.f2_cot, float)
        self.assertAlmostEqual(obj.f1_cot, 1 / math.tan(obj.f1))
        self.assertAlmostEqual(obj.f2_cot, 1 / math.tan(obj.f2))