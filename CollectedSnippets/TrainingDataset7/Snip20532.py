def test_integer(self):
        IntegerModel.objects.create(small=-1, normal=20, big=3)
        obj = IntegerModel.objects.annotate(
            small_power=Power("small", "normal"),
            normal_power=Power("normal", "big"),
            big_power=Power("big", "small"),
        ).first()
        self.assertIsInstance(obj.small_power, float)
        self.assertIsInstance(obj.normal_power, float)
        self.assertIsInstance(obj.big_power, float)
        self.assertAlmostEqual(obj.small_power, obj.small**obj.normal)
        self.assertAlmostEqual(obj.normal_power, obj.normal**obj.big)
        self.assertAlmostEqual(obj.big_power, obj.big**obj.small)