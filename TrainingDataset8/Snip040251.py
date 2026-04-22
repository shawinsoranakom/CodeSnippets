def test_get_command_line(self):
        """Test that _get_command_line_as_string correctly concatenates values
        from click.
        """
        mock_context = MagicMock()
        mock_context.parent.command_path = "streamlit"
        with patch("click.get_current_context", return_value=mock_context):
            with patch.object(sys, "argv", ["", "os_arg1", "os_arg2"]):
                result = cli._get_command_line_as_string()
                self.assertEqual("streamlit os_arg1 os_arg2", result)