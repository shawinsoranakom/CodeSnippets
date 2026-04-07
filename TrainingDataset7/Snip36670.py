def test_bad_role(self):
        self.assertIsNone(parse_color_setting("unknown="))
        self.assertIsNone(parse_color_setting("unknown=green"))
        self.assertEqual(
            parse_color_setting("unknown=green;sql_field=blue"),
            dict(PALETTES[NOCOLOR_PALETTE], SQL_FIELD={"fg": "blue"}),
        )