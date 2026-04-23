def test_mark_safe(self):
        s = mark_safe("a&b")

        self.assertRenderEqual("{{ s }}", "a&b", s=s)
        self.assertRenderEqual("{{ s|force_escape }}", "a&amp;b", s=s)