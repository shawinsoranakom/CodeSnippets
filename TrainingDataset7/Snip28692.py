def test_mixin_init(self):
        m = MixinModel()
        self.assertEqual(m.other_attr, 1)