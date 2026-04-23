def test_partial_runtime_exception_has_debug_info(self):
        template = self.engine.get_template("partial_with_variable_error")
        context = Context({})

        if hasattr(self.engine, "string_if_invalid") and self.engine.string_if_invalid:
            output = template.render(context)
            # The variable should be replaced with INVALID
            self.assertIn("INVALID", output)
        else:
            with self.assertRaises(VariableDoesNotExist) as cm:
                template.render(context)

            if self.engine.debug:
                exc_info = cm.exception.template_debug

                self.assertEqual(
                    exc_info["during"], "{{ nonexistent|default:alsonotthere }}"
                )
                self.assertEqual(exc_info["line"], 3)
                self.assertEqual(exc_info["name"], "partial_with_variable_error")
                self.assertIn("Failed lookup", exc_info["message"])