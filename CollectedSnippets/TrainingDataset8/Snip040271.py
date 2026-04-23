def test_reset_command(self):
        """Tests resetting a credential"""
        mock_credential = MagicMock()
        with mock.patch(
            "streamlit.runtime.credentials.Credentials.get_current",
            return_value=mock_credential,
        ):
            self.runner.invoke(cli, ["activate", "reset"])
            mock_credential.reset.assert_called()