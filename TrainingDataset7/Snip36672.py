def test_bad_option(self):
        self.assertEqual(
            parse_color_setting("error=green,unknown"),
            dict(PALETTES[NOCOLOR_PALETTE], ERROR={"fg": "green"}),
        )
        self.assertEqual(
            parse_color_setting("error=green,unknown,blink"),
            dict(PALETTES[NOCOLOR_PALETTE], ERROR={"fg": "green", "opts": ("blink",)}),
        )