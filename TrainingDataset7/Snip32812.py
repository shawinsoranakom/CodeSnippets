def test_add08(self):
        output = self.engine.render_to_string(
            "add08",
            {"s1": "string", "lazy_s2": gettext_lazy("lazy")},
        )
        self.assertEqual(output, "stringlazy")