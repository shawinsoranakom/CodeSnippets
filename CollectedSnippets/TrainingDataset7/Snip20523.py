def test_integer(self):
        IntegerModel.objects.create(small=4, normal=8, big=2)
        obj = IntegerModel.objects.annotate(
            small_log=Log("small", "big"),
            normal_log=Log("normal", "big"),
            big_log=Log("big", "big"),
        ).first()
        self.assertIsInstance(obj.small_log, float)
        self.assertIsInstance(obj.normal_log, float)
        self.assertIsInstance(obj.big_log, float)
        self.assertAlmostEqual(obj.small_log, math.log(obj.big, obj.small))
        self.assertAlmostEqual(obj.normal_log, math.log(obj.big, obj.normal))
        self.assertAlmostEqual(obj.big_log, math.log(obj.big, obj.big))