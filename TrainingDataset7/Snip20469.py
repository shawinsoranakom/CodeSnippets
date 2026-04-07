def test_integer(self):
        IntegerModel.objects.create(small=0, normal=1, big=-1)
        obj = IntegerModel.objects.annotate(
            small_acos=ACos("small"),
            normal_acos=ACos("normal"),
            big_acos=ACos("big"),
        ).first()
        self.assertIsInstance(obj.small_acos, float)
        self.assertIsInstance(obj.normal_acos, float)
        self.assertIsInstance(obj.big_acos, float)
        self.assertAlmostEqual(obj.small_acos, math.acos(obj.small))
        self.assertAlmostEqual(obj.normal_acos, math.acos(obj.normal))
        self.assertAlmostEqual(obj.big_acos, math.acos(obj.big))