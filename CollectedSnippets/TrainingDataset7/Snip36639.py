def test_add_lazy_safe_text_and_safe_text(self):
        s = html.escape(lazystr("a"))
        s += mark_safe("&b")
        self.assertRenderEqual("{{ s }}", "a&b", s=s)

        s = html.escapejs(lazystr("a"))
        s += mark_safe("&b")
        self.assertRenderEqual("{{ s }}", "a&b", s=s)