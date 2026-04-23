def test_float(self):
        FloatModel.objects.create(f1=2.0, f2=4.0)
        obj = FloatModel.objects.annotate(f_log=Log("f1", "f2")).first()
        self.assertIsInstance(obj.f_log, float)
        self.assertAlmostEqual(obj.f_log, math.log(obj.f2, obj.f1))