def test_override_with_multiple_roles(self):
        self.assertEqual(
            parse_color_setting("light;error=green;sql_field=blue"),
            dict(
                PALETTES[LIGHT_PALETTE], ERROR={"fg": "green"}, SQL_FIELD={"fg": "blue"}
            ),
        )