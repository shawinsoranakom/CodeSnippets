def test_include_template_iterable(self):
        engine = Engine.get_default()
        outer_temp = engine.from_string("{% include var %}")
        tests = [
            ("admin/fail.html", "index.html"),
            ["admin/fail.html", "index.html"],
        ]
        for template_names in tests:
            with self.subTest(template_names):
                output = outer_temp.render(Context({"var": template_names}))
                self.assertEqual(output, "index\n")