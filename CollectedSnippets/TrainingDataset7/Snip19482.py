def test_warning_unmatched_angle_brackets(self):
        self.assertEqual(
            check_url_config(None),
            [
                Warning(
                    "Your URL pattern 'beginning-with/<angle_bracket' has an unmatched "
                    "'<' bracket.",
                    id="urls.W010",
                ),
                Warning(
                    "Your URL pattern 'ending-with/angle_bracket>' has an unmatched "
                    "'>' bracket.",
                    id="urls.W010",
                ),
                Warning(
                    "Your URL pattern 'closed_angle>/x/<opened_angle' has an unmatched "
                    "'>' bracket.",
                    id="urls.W010",
                ),
                Warning(
                    "Your URL pattern 'closed_angle>/x/<opened_angle' has an unmatched "
                    "'<' bracket.",
                    id="urls.W010",
                ),
                Warning(
                    "Your URL pattern '<mixed>angle_bracket>' has an unmatched '>' "
                    "bracket.",
                    id="urls.W010",
                ),
            ],
        )