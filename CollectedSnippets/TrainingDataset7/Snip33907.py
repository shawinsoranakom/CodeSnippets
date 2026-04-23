def test_partial_with_syntax_error_exception_info(self):
        with self.assertRaises(TemplateSyntaxError) as cm:
            self.engine.get_template("partial_with_syntax_error")

        self.assertIn("endif", str(cm.exception).lower())

        if self.engine.debug:
            exc_debug = cm.exception.template_debug

            self.assertIn("endpartialdef", exc_debug["during"])
            self.assertEqual(exc_debug["name"], "partial_with_syntax_error")
            self.assertIn("endif", exc_debug["message"].lower())