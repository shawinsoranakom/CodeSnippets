def test_integer(self):
        IntegerModel.objects.create(small=-20, normal=0, big=20)
        obj = IntegerModel.objects.annotate(
            small_sign=Sign("small"),
            normal_sign=Sign("normal"),
            big_sign=Sign("big"),
        ).first()
        self.assertIsInstance(obj.small_sign, int)
        self.assertIsInstance(obj.normal_sign, int)
        self.assertIsInstance(obj.big_sign, int)
        self.assertEqual(obj.small_sign, -1)
        self.assertEqual(obj.normal_sign, 0)
        self.assertEqual(obj.big_sign, 1)