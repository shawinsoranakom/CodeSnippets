def test_null(self):
        IntegerModel.objects.create(big=100)
        obj = IntegerModel.objects.annotate(
            null_power_small=Power("small", "normal"),
            null_power_normal=Power("normal", "big"),
            null_power_big=Power("big", "normal"),
        ).first()
        self.assertIsNone(obj.null_power_small)
        self.assertIsNone(obj.null_power_normal)
        self.assertIsNone(obj.null_power_big)