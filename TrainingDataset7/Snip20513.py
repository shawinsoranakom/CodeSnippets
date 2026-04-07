def test_integer(self):
        IntegerModel.objects.create(small=-20, normal=15, big=-1)
        obj = IntegerModel.objects.annotate(
            small_floor=Floor("small"),
            normal_floor=Floor("normal"),
            big_floor=Floor("big"),
        ).first()
        self.assertIsInstance(obj.small_floor, int)
        self.assertIsInstance(obj.normal_floor, int)
        self.assertIsInstance(obj.big_floor, int)
        self.assertEqual(obj.small_floor, math.floor(obj.small))
        self.assertEqual(obj.normal_floor, math.floor(obj.normal))
        self.assertEqual(obj.big_floor, math.floor(obj.big))