def test_role_case(self):
        self.assertEqual(
            parse_color_setting("ERROR=green"),
            dict(PALETTES[NOCOLOR_PALETTE], ERROR={"fg": "green"}),
        )
        self.assertEqual(
            parse_color_setting("eRrOr=green"),
            dict(PALETTES[NOCOLOR_PALETTE], ERROR={"fg": "green"}),
        )