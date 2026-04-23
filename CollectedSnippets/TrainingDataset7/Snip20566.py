def test_integer(self):
        IntegerModel.objects.create(small=20, normal=15, big=1)
        obj = IntegerModel.objects.annotate(
            small_sqrt=Sqrt("small"),
            normal_sqrt=Sqrt("normal"),
            big_sqrt=Sqrt("big"),
        ).first()
        self.assertIsInstance(obj.small_sqrt, float)
        self.assertIsInstance(obj.normal_sqrt, float)
        self.assertIsInstance(obj.big_sqrt, float)
        self.assertAlmostEqual(obj.small_sqrt, math.sqrt(obj.small))
        self.assertAlmostEqual(obj.normal_sqrt, math.sqrt(obj.normal))
        self.assertAlmostEqual(obj.big_sqrt, math.sqrt(obj.big))