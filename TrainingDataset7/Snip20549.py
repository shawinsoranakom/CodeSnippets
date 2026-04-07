def test_integer_with_precision(self):
        IntegerModel.objects.create(small=-5, normal=3, big=-100)
        obj = IntegerModel.objects.annotate(
            small_round=Round("small", 1),
            normal_round=Round("normal", 5),
            big_round=Round("big", 2),
        ).first()
        self.assertIsInstance(obj.small_round, int)
        self.assertIsInstance(obj.normal_round, int)
        self.assertIsInstance(obj.big_round, int)
        self.assertAlmostEqual(obj.small_round, obj.small, places=1)
        self.assertAlmostEqual(obj.normal_round, obj.normal, places=5)
        self.assertAlmostEqual(obj.big_round, obj.big, places=2)