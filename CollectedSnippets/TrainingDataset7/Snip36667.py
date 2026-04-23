def test_empty_definition(self):
        self.assertIsNone(parse_color_setting(";"))
        self.assertEqual(parse_color_setting("light;"), PALETTES[LIGHT_PALETTE])
        self.assertIsNone(parse_color_setting(";;;"))