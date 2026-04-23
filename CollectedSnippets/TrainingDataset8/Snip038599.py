def test_get_options_for_section(self):
        config._set_option("theme.primaryColor", "000000", "test")
        config._set_option("theme.font", "serif", "test")

        expected = {
            "base": None,
            "primaryColor": "000000",
            "secondaryBackgroundColor": None,
            "backgroundColor": None,
            "textColor": None,
            "font": "serif",
        }
        self.assertEqual(config.get_options_for_section("theme"), expected)