def test_integer(self):
        IntegerModel.objects.create(small=-20, normal=15, big=-1)
        obj = IntegerModel.objects.annotate(
            small_degrees=Degrees("small"),
            normal_degrees=Degrees("normal"),
            big_degrees=Degrees("big"),
        ).first()
        self.assertIsInstance(obj.small_degrees, float)
        self.assertIsInstance(obj.normal_degrees, float)
        self.assertIsInstance(obj.big_degrees, float)
        self.assertAlmostEqual(obj.small_degrees, math.degrees(obj.small))
        self.assertAlmostEqual(obj.normal_degrees, math.degrees(obj.normal))
        self.assertAlmostEqual(obj.big_degrees, math.degrees(obj.big))