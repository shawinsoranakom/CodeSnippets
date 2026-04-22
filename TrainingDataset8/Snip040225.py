def test_print_new_version_message(self):
        with patch(
            "streamlit.version.should_show_new_version_notice", return_value=True
        ), patch("click.secho") as mock_echo:
            bootstrap._print_new_version_message()
            mock_echo.assert_called_once_with(NEW_VERSION_TEXT)