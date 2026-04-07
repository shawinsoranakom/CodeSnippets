def test_null(self):
        IntegerModel.objects.create(big=100)
        obj = IntegerModel.objects.annotate(
            null_mod_small=Mod("small", "normal"),
            null_mod_normal=Mod("normal", "big"),
        ).first()
        self.assertIsNone(obj.null_mod_small)
        self.assertIsNone(obj.null_mod_normal)