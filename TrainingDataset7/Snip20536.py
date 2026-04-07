def test_integer(self):
        IntegerModel.objects.create(small=-20, normal=15, big=-1)
        obj = IntegerModel.objects.annotate(
            small_radians=Radians("small"),
            normal_radians=Radians("normal"),
            big_radians=Radians("big"),
        ).first()
        self.assertIsInstance(obj.small_radians, float)
        self.assertIsInstance(obj.normal_radians, float)
        self.assertIsInstance(obj.big_radians, float)
        self.assertAlmostEqual(obj.small_radians, math.radians(obj.small))
        self.assertAlmostEqual(obj.normal_radians, math.radians(obj.normal))
        self.assertAlmostEqual(obj.big_radians, math.radians(obj.big))