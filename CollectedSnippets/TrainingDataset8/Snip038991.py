def test_get_over_max_options_message(
        self, current_selections, max_selections, expected_msg
    ):
        self.assertEqual(
            _get_over_max_options_message(current_selections, max_selections),
            expected_msg,
        )