def test_empty_options(self):
        self.assertEqual(
            parse_color_setting("error=green,"),
            dict(PALETTES[NOCOLOR_PALETTE], ERROR={"fg": "green"}),
        )
        self.assertEqual(
            parse_color_setting("error=green,,,"),
            dict(PALETTES[NOCOLOR_PALETTE], ERROR={"fg": "green"}),
        )
        self.assertEqual(
            parse_color_setting("error=green,,blink,,"),
            dict(PALETTES[NOCOLOR_PALETTE], ERROR={"fg": "green", "opts": ("blink",)}),
        )