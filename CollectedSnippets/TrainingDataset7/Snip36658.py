def test_fg(self):
        self.assertEqual(
            parse_color_setting("error=green"),
            dict(PALETTES[NOCOLOR_PALETTE], ERROR={"fg": "green"}),
        )