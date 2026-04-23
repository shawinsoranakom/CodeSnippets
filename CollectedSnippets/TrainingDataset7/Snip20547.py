def test_float_with_negative_precision(self):
        FloatModel.objects.create(f1=365.25)
        obj = FloatModel.objects.annotate(f1_round=Round("f1", -1)).first()
        self.assertIsInstance(obj.f1_round, float)
        self.assertEqual(obj.f1_round, 370)