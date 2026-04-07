def test_integer(self):
        IntegerModel.objects.create(small=-20, normal=15, big=-1)
        obj = IntegerModel.objects.annotate(
            small_tan=Tan("small"),
            normal_tan=Tan("normal"),
            big_tan=Tan("big"),
        ).first()
        self.assertIsInstance(obj.small_tan, float)
        self.assertIsInstance(obj.normal_tan, float)
        self.assertIsInstance(obj.big_tan, float)
        self.assertAlmostEqual(obj.small_tan, math.tan(obj.small))
        self.assertAlmostEqual(obj.normal_tan, math.tan(obj.normal))
        self.assertAlmostEqual(obj.big_tan, math.tan(obj.big))