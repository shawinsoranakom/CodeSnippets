def test_no_custom_theme_prop_if_no_theme(self, patched_config):
        patched_config.get_options_for_section.side_effect = (
            _mock_get_options_for_section(
                {
                    "base": None,
                    "primaryColor": None,
                    "backgroundColor": None,
                    "secondaryBackgroundColor": None,
                    "textColor": None,
                    "font": None,
                }
            )
        )

        msg = ForwardMsg()
        new_session_msg = msg.new_session
        app_session._populate_theme_msg(new_session_msg.custom_theme)

        self.assertEqual(new_session_msg.HasField("custom_theme"), False)