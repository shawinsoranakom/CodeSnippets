def test_get_command_line_without_parent_context(self):
        """Test that _get_command_line_as_string correctly returns None when
        there is no context parent
        """
        mock_context = MagicMock()
        mock_context.parent = None
        with patch("click.get_current_context", return_value=mock_context):
            result = cli._get_command_line_as_string()
            self.assertIsNone(result)