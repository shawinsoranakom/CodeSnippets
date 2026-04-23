def test_partial_runtime_error_exception_info(self):
        template = self.engine.get_template("partial_with_runtime_error")
        context = Context()

        with self.assertRaises(RuntimeError) as cm:
            template.render(context)

        if self.engine.debug:
            exc_debug = cm.exception.template_debug

            self.assertIn("badsimpletag", exc_debug["during"])
            self.assertEqual(exc_debug["line"], 5)  # Line 5 is where badsimpletag is
            self.assertEqual(exc_debug["name"], "partial_with_runtime_error")
            self.assertIn("bad simpletag", exc_debug["message"])