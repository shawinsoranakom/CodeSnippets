def test_initial_header_level(self):
        header = "should be h3...\n\nHeader\n------\n"
        output = parse_rst(header, "header")
        self.assertIn("<h3>Header</h3>", output)