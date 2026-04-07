def test_mark_safe_lazy(self):
        safe_s = mark_safe(lazystr("a&b"))

        self.assertIsInstance(safe_s, Promise)
        self.assertRenderEqual("{{ s }}", "a&b", s=safe_s)
        self.assertIsInstance(str(safe_s), SafeData)