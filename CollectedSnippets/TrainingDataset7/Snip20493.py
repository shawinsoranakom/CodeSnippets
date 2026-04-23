def test_integer(self):
        IntegerModel.objects.create(small=-20, normal=15, big=-1)
        obj = IntegerModel.objects.annotate(
            small_cos=Cos("small"),
            normal_cos=Cos("normal"),
            big_cos=Cos("big"),
        ).first()
        self.assertIsInstance(obj.small_cos, float)
        self.assertIsInstance(obj.normal_cos, float)
        self.assertIsInstance(obj.big_cos, float)
        self.assertAlmostEqual(obj.small_cos, math.cos(obj.small))
        self.assertAlmostEqual(obj.normal_cos, math.cos(obj.normal))
        self.assertAlmostEqual(obj.big_cos, math.cos(obj.big))