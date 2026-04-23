def test_color_case(self):
        self.assertEqual(
            parse_color_setting("error=GREEN"),
            dict(PALETTES[NOCOLOR_PALETTE], ERROR={"fg": "green"}),
        )
        self.assertEqual(
            parse_color_setting("error=GREEN/BLUE"),
            dict(PALETTES[NOCOLOR_PALETTE], ERROR={"fg": "green", "bg": "blue"}),
        )
        self.assertEqual(
            parse_color_setting("error=gReEn"),
            dict(PALETTES[NOCOLOR_PALETTE], ERROR={"fg": "green"}),
        )
        self.assertEqual(
            parse_color_setting("error=gReEn/bLuE"),
            dict(PALETTES[NOCOLOR_PALETTE], ERROR={"fg": "green", "bg": "blue"}),
        )