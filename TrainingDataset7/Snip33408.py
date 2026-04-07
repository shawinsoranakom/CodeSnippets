def test_basic_syntax03(self):
        """
        More than one replacement variable is allowed in a template
        """
        output = self.engine.render_to_string(
            "basic-syntax03", {"first": 1, "second": 2}
        )
        self.assertEqual(output, "1 --- 2")