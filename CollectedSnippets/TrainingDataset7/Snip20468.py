def test_float(self):
        FloatModel.objects.create(f1=-0.5, f2=0.33)
        obj = FloatModel.objects.annotate(
            f1_acos=ACos("f1"), f2_acos=ACos("f2")
        ).first()
        self.assertIsInstance(obj.f1_acos, float)
        self.assertIsInstance(obj.f2_acos, float)
        self.assertAlmostEqual(obj.f1_acos, math.acos(obj.f1))
        self.assertAlmostEqual(obj.f2_acos, math.acos(obj.f2))