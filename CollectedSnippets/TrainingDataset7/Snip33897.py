def test_partial_in_included_template(self):
        output = self.engine.render_to_string("partial_with_include")
        expected = (
            "MAIN TEMPLATE START\nINCLUDED TEMPLATE START\n\n\n"
            "Now using the partial: \n"
            "THIS IS CONTENT FROM THE INCLUDED PARTIAL\n\n"
            "INCLUDED TEMPLATE END\n\nMAIN TEMPLATE END"
        )
        self.assertEqual(output, expected)