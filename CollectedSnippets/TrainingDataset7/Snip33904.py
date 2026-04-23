def test_partial_template_get_exception_info_delegation(self):
        if self.engine.debug:
            template = self.engine.get_template("partial_exception_info_test")

            partial_template = template.extra_data["partials"]["testing-name"]

            test_exc = Exception("Test exception")
            token = Token(
                token_type=TokenType.VAR,
                contents="test",
                position=(0, 4),
            )

            exc_info = partial_template.get_exception_info(test_exc, token)
            self.assertIn("message", exc_info)
            self.assertIn("line", exc_info)
            self.assertIn("name", exc_info)
            self.assertEqual(exc_info["name"], "partial_exception_info_test")
            self.assertEqual(exc_info["message"], "Test exception")