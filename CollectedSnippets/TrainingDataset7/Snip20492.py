def test_float(self):
        FloatModel.objects.create(f1=-27.5, f2=0.33)
        obj = FloatModel.objects.annotate(f1_cos=Cos("f1"), f2_cos=Cos("f2")).first()
        self.assertIsInstance(obj.f1_cos, float)
        self.assertIsInstance(obj.f2_cos, float)
        self.assertAlmostEqual(obj.f1_cos, math.cos(obj.f1))
        self.assertAlmostEqual(obj.f2_cos, math.cos(obj.f2))