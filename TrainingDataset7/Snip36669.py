def test_bad_palette(self):
        self.assertIsNone(parse_color_setting("unknown"))