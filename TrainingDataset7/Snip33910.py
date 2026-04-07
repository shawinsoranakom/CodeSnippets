def test_partial_in_extended_template_error(self):
        with self.assertRaises(TemplateSyntaxError) as cm:
            self.engine.get_template("child.html")

        self.assertIn("undefined_filter", str(cm.exception))

        if self.engine.debug:
            exc_debug = cm.exception.template_debug

            self.assertIn("undefined_filter", exc_debug["during"])
            self.assertEqual(exc_debug["name"], "child.html")
            self.assertIn("undefined_filter", exc_debug["message"])