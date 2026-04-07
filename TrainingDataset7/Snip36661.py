def test_fg_bg_opts(self):
        self.assertEqual(
            parse_color_setting("error=green/blue,blink"),
            dict(
                PALETTES[NOCOLOR_PALETTE],
                ERROR={"fg": "green", "bg": "blue", "opts": ("blink",)},
            ),
        )
        self.assertEqual(
            parse_color_setting("error=green/blue,bold,blink"),
            dict(
                PALETTES[NOCOLOR_PALETTE],
                ERROR={"fg": "green", "bg": "blue", "opts": ("blink", "bold")},
            ),
        )