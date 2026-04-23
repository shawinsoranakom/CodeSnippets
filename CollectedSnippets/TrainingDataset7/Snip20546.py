def test_float_with_precision(self):
        FloatModel.objects.create(f1=-5.75, f2=Pi())
        obj = FloatModel.objects.annotate(
            f1_round=Round("f1", 1),
            f2_round=Round("f2", 5),
        ).first()
        self.assertIsInstance(obj.f1_round, float)
        self.assertIsInstance(obj.f2_round, float)
        self.assertAlmostEqual(obj.f1_round, obj.f1, places=1)
        self.assertAlmostEqual(obj.f2_round, obj.f2, places=5)