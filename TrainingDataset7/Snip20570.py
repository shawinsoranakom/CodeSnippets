def test_float(self):
        FloatModel.objects.create(f1=-27.5, f2=0.33)
        obj = FloatModel.objects.annotate(f1_tan=Tan("f1"), f2_tan=Tan("f2")).first()
        self.assertIsInstance(obj.f1_tan, float)
        self.assertIsInstance(obj.f2_tan, float)
        self.assertAlmostEqual(obj.f1_tan, math.tan(obj.f1))
        self.assertAlmostEqual(obj.f2_tan, math.tan(obj.f2))