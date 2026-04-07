def test_integer(self):
        IntegerModel.objects.create(small=-20, normal=15, big=-1)
        obj = IntegerModel.objects.annotate(
            small_round=Round("small"),
            normal_round=Round("normal"),
            big_round=Round("big"),
        ).first()
        self.assertIsInstance(obj.small_round, int)
        self.assertIsInstance(obj.normal_round, int)
        self.assertIsInstance(obj.big_round, int)
        self.assertAlmostEqual(obj.small_round, obj.small, places=0)
        self.assertAlmostEqual(obj.normal_round, obj.normal, places=0)
        self.assertAlmostEqual(obj.big_round, obj.big, places=0)