def test_float(self):
        FloatModel.objects.create(f1=-27.5, f2=0.33)
        obj = FloatModel.objects.annotate(
            f1_degrees=Degrees("f1"), f2_degrees=Degrees("f2")
        ).first()
        self.assertIsInstance(obj.f1_degrees, float)
        self.assertIsInstance(obj.f2_degrees, float)
        self.assertAlmostEqual(obj.f1_degrees, math.degrees(obj.f1))
        self.assertAlmostEqual(obj.f2_degrees, math.degrees(obj.f2))