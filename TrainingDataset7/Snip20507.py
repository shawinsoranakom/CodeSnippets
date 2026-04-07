def test_float(self):
        FloatModel.objects.create(f1=-27.5, f2=0.33)
        obj = FloatModel.objects.annotate(f1_exp=Exp("f1"), f2_exp=Exp("f2")).first()
        self.assertIsInstance(obj.f1_exp, float)
        self.assertIsInstance(obj.f2_exp, float)
        self.assertAlmostEqual(obj.f1_exp, math.exp(obj.f1))
        self.assertAlmostEqual(obj.f2_exp, math.exp(obj.f2))