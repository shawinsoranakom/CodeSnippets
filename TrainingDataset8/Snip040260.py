def test_docs_command(self):
        """Tests the docs command opens the browser"""
        with patch("streamlit.util.open_browser") as mock_open_browser:
            self.runner.invoke(cli, ["docs"])
            mock_open_browser.assert_called_once_with("https://docs.streamlit.io")