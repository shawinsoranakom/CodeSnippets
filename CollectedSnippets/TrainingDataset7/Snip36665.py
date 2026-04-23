def test_multiple_roles(self):
        self.assertEqual(
            parse_color_setting("error=green;sql_field=blue"),
            dict(
                PALETTES[NOCOLOR_PALETTE],
                ERROR={"fg": "green"},
                SQL_FIELD={"fg": "blue"},
            ),
        )