def test_float(self):
        FloatModel.objects.create(f1=-27.5, f2=0.33)
        obj = FloatModel.objects.annotate(
            f1_sign=Sign("f1"), f2_sign=Sign("f2")
        ).first()
        self.assertIsInstance(obj.f1_sign, float)
        self.assertIsInstance(obj.f2_sign, float)
        self.assertEqual(obj.f1_sign, -1.0)
        self.assertEqual(obj.f2_sign, 1.0)