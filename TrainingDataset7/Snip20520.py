def test_null(self):
        IntegerModel.objects.create(big=100)
        obj = IntegerModel.objects.annotate(
            null_log_small=Log("small", "normal"),
            null_log_normal=Log("normal", "big"),
            null_log_big=Log("big", "normal"),
        ).first()
        self.assertIsNone(obj.null_log_small)
        self.assertIsNone(obj.null_log_normal)
        self.assertIsNone(obj.null_log_big)