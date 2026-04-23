def test_can_specify_all_options(self, patched_config):
        patched_config.get_options_for_section.side_effect = (
            # Specifies all options by default.
            _mock_get_options_for_section()
        )

        msg = ForwardMsg()
        new_session_msg = msg.new_session
        app_session._populate_theme_msg(new_session_msg.custom_theme)

        self.assertEqual(new_session_msg.HasField("custom_theme"), True)
        self.assertEqual(new_session_msg.custom_theme.primary_color, "coral")
        self.assertEqual(new_session_msg.custom_theme.background_color, "white")