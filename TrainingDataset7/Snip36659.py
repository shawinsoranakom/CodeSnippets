def test_fg_bg(self):
        self.assertEqual(
            parse_color_setting("error=green/blue"),
            dict(PALETTES[NOCOLOR_PALETTE], ERROR={"fg": "green", "bg": "blue"}),
        )