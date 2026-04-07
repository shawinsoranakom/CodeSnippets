def test_integer(self):
        IntegerModel.objects.create(small=-11, normal=0, big=-100)
        obj = IntegerModel.objects.annotate(
            small_ceil=Ceil("small"),
            normal_ceil=Ceil("normal"),
            big_ceil=Ceil("big"),
        ).first()
        self.assertIsInstance(obj.small_ceil, int)
        self.assertIsInstance(obj.normal_ceil, int)
        self.assertIsInstance(obj.big_ceil, int)
        self.assertEqual(obj.small_ceil, math.ceil(obj.small))
        self.assertEqual(obj.normal_ceil, math.ceil(obj.normal))
        self.assertEqual(obj.big_ceil, math.ceil(obj.big))