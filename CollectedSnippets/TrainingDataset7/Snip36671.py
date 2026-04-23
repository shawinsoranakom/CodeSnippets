def test_bad_color(self):
        self.assertIsNone(parse_color_setting("error="))
        self.assertEqual(
            parse_color_setting("error=;sql_field=blue"),
            dict(PALETTES[NOCOLOR_PALETTE], SQL_FIELD={"fg": "blue"}),
        )
        self.assertIsNone(parse_color_setting("error=unknown"))
        self.assertEqual(
            parse_color_setting("error=unknown;sql_field=blue"),
            dict(PALETTES[NOCOLOR_PALETTE], SQL_FIELD={"fg": "blue"}),
        )
        self.assertEqual(
            parse_color_setting("error=green/unknown"),
            dict(PALETTES[NOCOLOR_PALETTE], ERROR={"fg": "green"}),
        )
        self.assertEqual(
            parse_color_setting("error=green/blue/something"),
            dict(PALETTES[NOCOLOR_PALETTE], ERROR={"fg": "green", "bg": "blue"}),
        )
        self.assertEqual(
            parse_color_setting("error=green/blue/something,blink"),
            dict(
                PALETTES[NOCOLOR_PALETTE],
                ERROR={"fg": "green", "bg": "blue", "opts": ("blink",)},
            ),
        )