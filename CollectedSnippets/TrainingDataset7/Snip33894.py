def test_partial_used_before_definition(self):
        output = self.engine.render_to_string("partial_used_before_definition")
        expected = (
            "TEMPLATE START\n\nTHIS IS THE PARTIAL CONTENT\n\n"
            "MIDDLE CONTENT\n\nTEMPLATE END"
        )
        self.assertEqual(output, expected)