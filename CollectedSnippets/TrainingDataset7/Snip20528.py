def test(self):
        FloatModel.objects.create(f1=2.5, f2=15.9)
        obj = FloatModel.objects.annotate(pi=Pi()).first()
        self.assertIsInstance(obj.pi, float)
        self.assertAlmostEqual(obj.pi, math.pi, places=5)