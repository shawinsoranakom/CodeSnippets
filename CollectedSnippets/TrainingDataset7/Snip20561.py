def test_integer(self):
        IntegerModel.objects.create(small=-20, normal=15, big=-1)
        obj = IntegerModel.objects.annotate(
            small_sin=Sin("small"),
            normal_sin=Sin("normal"),
            big_sin=Sin("big"),
        ).first()
        self.assertIsInstance(obj.small_sin, float)
        self.assertIsInstance(obj.normal_sin, float)
        self.assertIsInstance(obj.big_sin, float)
        self.assertAlmostEqual(obj.small_sin, math.sin(obj.small))
        self.assertAlmostEqual(obj.normal_sin, math.sin(obj.normal))
        self.assertAlmostEqual(obj.big_sin, math.sin(obj.big))