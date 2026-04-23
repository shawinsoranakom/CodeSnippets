def test_integer(self):
        IntegerModel.objects.create(small=-20, normal=15, big=-1)
        obj = IntegerModel.objects.annotate(
            small_atan=ATan("small"),
            normal_atan=ATan("normal"),
            big_atan=ATan("big"),
        ).first()
        self.assertIsInstance(obj.small_atan, float)
        self.assertIsInstance(obj.normal_atan, float)
        self.assertIsInstance(obj.big_atan, float)
        self.assertAlmostEqual(obj.small_atan, math.atan(obj.small))
        self.assertAlmostEqual(obj.normal_atan, math.atan(obj.normal))
        self.assertAlmostEqual(obj.big_atan, math.atan(obj.big))