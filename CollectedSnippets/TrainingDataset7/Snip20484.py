def test_integer(self):
        IntegerModel.objects.create(small=0, normal=1, big=10)
        obj = IntegerModel.objects.annotate(
            atan2_sn=ATan2("small", "normal"),
            atan2_nb=ATan2("normal", "big"),
        ).first()
        self.assertIsInstance(obj.atan2_sn, float)
        self.assertIsInstance(obj.atan2_nb, float)
        self.assertAlmostEqual(obj.atan2_sn, math.atan2(obj.small, obj.normal))
        self.assertAlmostEqual(obj.atan2_nb, math.atan2(obj.normal, obj.big))