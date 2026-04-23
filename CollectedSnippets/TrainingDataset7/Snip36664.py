def test_reverse_override(self):
        self.assertEqual(
            parse_color_setting("error=green;light"), PALETTES[LIGHT_PALETTE]
        )