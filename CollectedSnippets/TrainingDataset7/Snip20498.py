def test_integer(self):
        IntegerModel.objects.create(small=-5, normal=15, big=-1)
        obj = IntegerModel.objects.annotate(
            small_cot=Cot("small"),
            normal_cot=Cot("normal"),
            big_cot=Cot("big"),
        ).first()
        self.assertIsInstance(obj.small_cot, float)
        self.assertIsInstance(obj.normal_cot, float)
        self.assertIsInstance(obj.big_cot, float)
        self.assertAlmostEqual(obj.small_cot, 1 / math.tan(obj.small))
        self.assertAlmostEqual(obj.normal_cot, 1 / math.tan(obj.normal))
        self.assertAlmostEqual(obj.big_cot, 1 / math.tan(obj.big))