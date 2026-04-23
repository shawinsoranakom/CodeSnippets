def test_nested_partial_error_exception_info(self):
        template = self.engine.get_template("nested_partial_with_undefined_var")
        context = Context()
        output = template.render(context)

        # When string_if_invalid is set, it will show INVALID
        # When not set, undefined variables just render as empty string
        if hasattr(self.engine, "string_if_invalid") and self.engine.string_if_invalid:
            self.assertIn("INVALID", output)
        else:
            self.assertIn("<p>", output)
            self.assertIn("</p>", output)