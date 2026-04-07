def test_add_str(self):
        s = SafeString("a&b")
        cases = [
            ("test", "a&amp;btest"),
            ("<p>unsafe</p>", "a&amp;b&lt;p&gt;unsafe&lt;/p&gt;"),
            (SafeString("<p>safe</p>"), SafeString("a&b<p>safe</p>")),
        ]
        for case, expected in cases:
            with self.subTest(case=case):
                self.assertRenderEqual("{{ s }}", expected, s=s + case)