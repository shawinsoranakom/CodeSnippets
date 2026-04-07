def test_float(self):
        FloatModel.objects.create(f1=-27.55, f2=0.55)
        obj = FloatModel.objects.annotate(
            f1_round=Round("f1"), f2_round=Round("f2")
        ).first()
        self.assertIsInstance(obj.f1_round, float)
        self.assertIsInstance(obj.f2_round, float)
        self.assertAlmostEqual(obj.f1_round, obj.f1, places=0)
        self.assertAlmostEqual(obj.f2_round, obj.f2, places=0)