def test_opts_case(self):
        self.assertEqual(
            parse_color_setting("error=green,BLINK"),
            dict(PALETTES[NOCOLOR_PALETTE], ERROR={"fg": "green", "opts": ("blink",)}),
        )
        self.assertEqual(
            parse_color_setting("error=green,bLiNk"),
            dict(PALETTES[NOCOLOR_PALETTE], ERROR={"fg": "green", "opts": ("blink",)}),
        )