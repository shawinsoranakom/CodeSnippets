def test_truncatewords02(self):
        output = self.engine.render_to_string(
            "truncatewords02",
            {"a": "alpha & bravo", "b": mark_safe("alpha &amp; bravo")},
        )
        self.assertEqual(output, "alpha &amp; … alpha &amp; …")