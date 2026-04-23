def test_float(self):
        FloatModel.objects.create(f1=-27.5, f2=0.33)
        obj = FloatModel.objects.annotate(
            f1_radians=Radians("f1"), f2_radians=Radians("f2")
        ).first()
        self.assertIsInstance(obj.f1_radians, float)
        self.assertIsInstance(obj.f2_radians, float)
        self.assertAlmostEqual(obj.f1_radians, math.radians(obj.f1))
        self.assertAlmostEqual(obj.f2_radians, math.radians(obj.f2))