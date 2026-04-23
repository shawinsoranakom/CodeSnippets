def test_fg_opts(self):
        self.assertEqual(
            parse_color_setting("error=green,blink"),
            dict(PALETTES[NOCOLOR_PALETTE], ERROR={"fg": "green", "opts": ("blink",)}),
        )
        self.assertEqual(
            parse_color_setting("error=green,bold,blink"),
            dict(
                PALETTES[NOCOLOR_PALETTE],
                ERROR={"fg": "green", "opts": ("blink", "bold")},
            ),
        )