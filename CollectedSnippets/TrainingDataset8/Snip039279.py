def test_logs_warning_if_base_invalid(self, patched_config, patched_logger):
        patched_config.get_options_for_section.side_effect = (
            _mock_get_options_for_section({"base": "blah"})
        )

        msg = ForwardMsg()
        new_session_msg = msg.new_session
        app_session._populate_theme_msg(new_session_msg.custom_theme)

        patched_logger.warning.assert_called_once_with(
            '"blah" is an invalid value for theme.base.'
            " Allowed values include ['light', 'dark']. Setting theme.base to \"light\"."
        )