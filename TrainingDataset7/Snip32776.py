def test_template_render_error_nonexistent_source(self):
        template = self.engine.get_template("template_backends/hello.html")
        with mock.patch(
            "jinja2.environment.Template.render",
            side_effect=jinja2.TemplateSyntaxError("", 1, filename="nonexistent.html"),
        ):
            with self.assertRaises(TemplateSyntaxError) as e:
                template.render(context={})
        debug = e.exception.template_debug
        self.assertEqual(debug["after"], "")
        self.assertEqual(debug["before"], "")
        self.assertEqual(debug["during"], "")
        self.assertEqual(debug["bottom"], 0)
        self.assertEqual(debug["top"], 0)
        self.assertEqual(debug["line"], 1)
        self.assertEqual(debug["total"], 0)
        self.assertEqual(len(debug["source_lines"]), 0)
        self.assertTrue(debug["name"].endswith("nonexistent.html"))
        self.assertIn("message", debug)