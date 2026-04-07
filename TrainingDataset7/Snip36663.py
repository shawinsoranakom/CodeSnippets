def test_override_nocolor(self):
        self.assertEqual(
            parse_color_setting("nocolor;error=green"),
            dict(PALETTES[NOCOLOR_PALETTE], ERROR={"fg": "green"}),
        )