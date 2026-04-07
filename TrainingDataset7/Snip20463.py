def test_float(self):
        obj = FloatModel.objects.create(f1=-0.5, f2=12)
        obj = FloatModel.objects.annotate(f1_abs=Abs("f1"), f2_abs=Abs("f2")).first()
        self.assertIsInstance(obj.f1_abs, float)
        self.assertIsInstance(obj.f2_abs, float)
        self.assertEqual(obj.f1, -obj.f1_abs)
        self.assertEqual(obj.f2, obj.f2_abs)