def test_float(self):
        FloatModel.objects.create(f1=-27.5, f2=0.33)
        obj = FloatModel.objects.annotate(f1_sin=Sin("f1"), f2_sin=Sin("f2")).first()
        self.assertIsInstance(obj.f1_sin, float)
        self.assertIsInstance(obj.f2_sin, float)
        self.assertAlmostEqual(obj.f1_sin, math.sin(obj.f1))
        self.assertAlmostEqual(obj.f2_sin, math.sin(obj.f2))