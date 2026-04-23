def test_float(self):
        FloatModel.objects.create(f1=-12.5, f2=21.33)
        obj = FloatModel.objects.annotate(
            f1_ceil=Ceil("f1"), f2_ceil=Ceil("f2")
        ).first()
        self.assertIsInstance(obj.f1_ceil, float)
        self.assertIsInstance(obj.f2_ceil, float)
        self.assertEqual(obj.f1_ceil, math.ceil(obj.f1))
        self.assertEqual(obj.f2_ceil, math.ceil(obj.f2))