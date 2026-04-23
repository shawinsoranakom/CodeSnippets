def test_float(self):
        FloatModel.objects.create(f1=-25, f2=0.33)
        obj = FloatModel.objects.annotate(f_atan2=ATan2("f1", "f2")).first()
        self.assertIsInstance(obj.f_atan2, float)
        self.assertAlmostEqual(obj.f_atan2, math.atan2(obj.f1, obj.f2))