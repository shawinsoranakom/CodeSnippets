def test_integer(self):
        IntegerModel.objects.create(small=20, normal=15, big=1)
        obj = IntegerModel.objects.annotate(
            small_ln=Ln("small"),
            normal_ln=Ln("normal"),
            big_ln=Ln("big"),
        ).first()
        self.assertIsInstance(obj.small_ln, float)
        self.assertIsInstance(obj.normal_ln, float)
        self.assertIsInstance(obj.big_ln, float)
        self.assertAlmostEqual(obj.small_ln, math.log(obj.small))
        self.assertAlmostEqual(obj.normal_ln, math.log(obj.normal))
        self.assertAlmostEqual(obj.big_ln, math.log(obj.big))