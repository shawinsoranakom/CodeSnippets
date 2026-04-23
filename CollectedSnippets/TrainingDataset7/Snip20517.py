def test_float(self):
        FloatModel.objects.create(f1=27.5, f2=0.33)
        obj = FloatModel.objects.annotate(f1_ln=Ln("f1"), f2_ln=Ln("f2")).first()
        self.assertIsInstance(obj.f1_ln, float)
        self.assertIsInstance(obj.f2_ln, float)
        self.assertAlmostEqual(obj.f1_ln, math.log(obj.f1))
        self.assertAlmostEqual(obj.f2_ln, math.log(obj.f2))