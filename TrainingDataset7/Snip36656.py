def test_empty_string(self):
        self.assertEqual(parse_color_setting(""), PALETTES[DEFAULT_PALETTE])