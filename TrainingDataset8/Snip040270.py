def test_activate_without_command(self):
        """Tests that it doesn't activate the credential when not specified"""
        mock_credential = MagicMock()
        with mock.patch(
            "streamlit.runtime.credentials.Credentials.get_current",
            return_value=mock_credential,
        ):
            self.runner.invoke(cli)
            mock_credential.activate.assert_not_called()