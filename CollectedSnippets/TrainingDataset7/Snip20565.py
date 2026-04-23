def test_float(self):
        FloatModel.objects.create(f1=27.5, f2=0.33)
        obj = FloatModel.objects.annotate(
            f1_sqrt=Sqrt("f1"), f2_sqrt=Sqrt("f2")
        ).first()
        self.assertIsInstance(obj.f1_sqrt, float)
        self.assertIsInstance(obj.f2_sqrt, float)
        self.assertAlmostEqual(obj.f1_sqrt, math.sqrt(obj.f1))
        self.assertAlmostEqual(obj.f2_sqrt, math.sqrt(obj.f2))