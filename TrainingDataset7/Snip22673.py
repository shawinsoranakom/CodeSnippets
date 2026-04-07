def test_slugfield_unicode_normalization(self):
        f = SlugField(allow_unicode=True)
        self.assertEqual(f.clean("a"), "a")
        self.assertEqual(f.clean("1"), "1")
        self.assertEqual(f.clean("a1"), "a1")
        self.assertEqual(f.clean("你好"), "你好")
        self.assertEqual(f.clean("  你-好  "), "你-好")
        self.assertEqual(f.clean("ıçğüş"), "ıçğüş")
        self.assertEqual(f.clean("foo-ıç-bar"), "foo-ıç-bar")