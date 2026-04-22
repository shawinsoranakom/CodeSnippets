def test_activate_command(self):
        """Tests activating a credential"""
        mock_credential = MagicMock()
        with mock.patch(
            "streamlit.runtime.credentials.Credentials.get_current",
            return_value=mock_credential,
        ):
            self.runner.invoke(cli, ["activate"])
            mock_credential.activate.assert_called()