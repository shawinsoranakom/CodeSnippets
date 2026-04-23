def test_integer(self):
        IntegerModel.objects.create(small=12, normal=0, big=-45)
        obj = IntegerModel.objects.annotate(
            small_abs=Abs("small"),
            normal_abs=Abs("normal"),
            big_abs=Abs("big"),
        ).first()
        self.assertIsInstance(obj.small_abs, int)
        self.assertIsInstance(obj.normal_abs, int)
        self.assertIsInstance(obj.big_abs, int)
        self.assertEqual(obj.small, obj.small_abs)
        self.assertEqual(obj.normal, obj.normal_abs)
        self.assertEqual(obj.big, -obj.big_abs)