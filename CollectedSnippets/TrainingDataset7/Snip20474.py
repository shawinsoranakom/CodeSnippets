def test_integer(self):
        IntegerModel.objects.create(small=0, normal=1, big=-1)
        obj = IntegerModel.objects.annotate(
            small_asin=ASin("small"),
            normal_asin=ASin("normal"),
            big_asin=ASin("big"),
        ).first()
        self.assertIsInstance(obj.small_asin, float)
        self.assertIsInstance(obj.normal_asin, float)
        self.assertIsInstance(obj.big_asin, float)
        self.assertAlmostEqual(obj.small_asin, math.asin(obj.small))
        self.assertAlmostEqual(obj.normal_asin, math.asin(obj.normal))
        self.assertAlmostEqual(obj.big_asin, math.asin(obj.big))