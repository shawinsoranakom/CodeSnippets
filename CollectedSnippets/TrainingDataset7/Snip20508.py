def test_integer(self):
        IntegerModel.objects.create(small=-20, normal=15, big=-1)
        obj = IntegerModel.objects.annotate(
            small_exp=Exp("small"),
            normal_exp=Exp("normal"),
            big_exp=Exp("big"),
        ).first()
        self.assertIsInstance(obj.small_exp, float)
        self.assertIsInstance(obj.normal_exp, float)
        self.assertIsInstance(obj.big_exp, float)
        self.assertAlmostEqual(obj.small_exp, math.exp(obj.small))
        self.assertAlmostEqual(obj.normal_exp, math.exp(obj.normal))
        self.assertAlmostEqual(obj.big_exp, math.exp(obj.big))