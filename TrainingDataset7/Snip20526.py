def test_float(self):
        FloatModel.objects.create(f1=-25, f2=0.33)
        obj = FloatModel.objects.annotate(f_mod=Mod("f1", "f2")).first()
        self.assertIsInstance(obj.f_mod, float)
        self.assertAlmostEqual(obj.f_mod, math.fmod(obj.f1, obj.f2))