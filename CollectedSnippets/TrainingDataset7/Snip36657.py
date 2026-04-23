def test_simple_palette(self):
        self.assertEqual(parse_color_setting("light"), PALETTES[LIGHT_PALETTE])
        self.assertEqual(parse_color_setting("dark"), PALETTES[DARK_PALETTE])
        self.assertIsNone(parse_color_setting("nocolor"))