def test_integer(self):
        IntegerModel.objects.create(small=20, normal=15, big=1)
        obj = IntegerModel.objects.annotate(
            small_mod=Mod("small", "normal"),
            normal_mod=Mod("normal", "big"),
            big_mod=Mod("big", "small"),
        ).first()
        self.assertIsInstance(obj.small_mod, float)
        self.assertIsInstance(obj.normal_mod, float)
        self.assertIsInstance(obj.big_mod, float)
        self.assertEqual(obj.small_mod, math.fmod(obj.small, obj.normal))
        self.assertEqual(obj.normal_mod, math.fmod(obj.normal, obj.big))
        self.assertEqual(obj.big_mod, math.fmod(obj.big, obj.small))