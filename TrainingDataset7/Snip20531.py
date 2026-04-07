def test_float(self):
        FloatModel.objects.create(f1=2.3, f2=1.1)
        obj = FloatModel.objects.annotate(f_power=Power("f1", "f2")).first()
        self.assertIsInstance(obj.f_power, float)
        self.assertAlmostEqual(obj.f_power, obj.f1**obj.f2)