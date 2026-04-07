def test_float(self):
        FloatModel.objects.create(f1=-27.5, f2=0.33)
        obj = FloatModel.objects.annotate(
            f1_atan=ATan("f1"), f2_atan=ATan("f2")
        ).first()
        self.assertIsInstance(obj.f1_atan, float)
        self.assertIsInstance(obj.f2_atan, float)
        self.assertAlmostEqual(obj.f1_atan, math.atan(obj.f1))
        self.assertAlmostEqual(obj.f2_atan, math.atan(obj.f2))