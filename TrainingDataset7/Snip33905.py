def test_undefined_partial_exception_info(self):
        template = self.engine.get_template("partial_with_undefined_reference")
        with self.assertRaises(TemplateSyntaxError) as cm:
            template.render(Context())

        self.assertIn("undefined", str(cm.exception))
        self.assertIn("is not defined", str(cm.exception))

        if self.engine.debug:
            exc_debug = cm.exception.template_debug

            self.assertEqual(exc_debug["during"], "{% partial undefined %}")
            self.assertEqual(exc_debug["line"], 2)
            self.assertEqual(exc_debug["name"], "partial_with_undefined_reference")
            self.assertIn("undefined", exc_debug["message"])