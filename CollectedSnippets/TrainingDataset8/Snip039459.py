def test_Credentials_reset_error(self):
        """Test Credentials.reset() with error."""
        with patch(
            "streamlit.runtime.credentials.os.remove", side_effect=OSError("some error")
        ), patch("streamlit.runtime.credentials.LOGGER") as p:

            Credentials.reset()
            p.error.assert_called_once_with(
                "Error removing credentials file: some error"
            )