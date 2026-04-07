def test_add09(self):
        output = self.engine.render_to_string(
            "add09",
            {"lazy_s1": gettext_lazy("string"), "lazy_s2": gettext_lazy("lazy")},
        )
        self.assertEqual(output, "stringlazy")