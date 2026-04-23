def test_override_palette(self):
        self.assertEqual(
            parse_color_setting("light;error=green"),
            dict(PALETTES[LIGHT_PALETTE], ERROR={"fg": "green"}),
        )