def test_mark_safe_object_implementing_dunder_html(self):
        e = customescape("<a&b>")
        s = mark_safe(e)
        self.assertIs(s, e)

        self.assertRenderEqual("{{ s }}", "<<a&b>>", s=s)
        self.assertRenderEqual("{{ s|force_escape }}", "&lt;a&amp;b&gt;", s=s)