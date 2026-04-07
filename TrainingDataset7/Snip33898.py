def test_partial_as_include_in_template(self):
        output = self.engine.render_to_string("partial_as_include_in_other_template")
        expected = (
            "MAIN TEMPLATE START\n\n"
            "THIS IS CONTENT FROM THE INCLUDED PARTIAL\n\n"
            "MAIN TEMPLATE END"
        )
        self.assertEqual(output, expected)