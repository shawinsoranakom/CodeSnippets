def test_is_url_from_allowed_origins_browser_serverAddress(self):
        with patch(
            "streamlit.web.server.server_util.config.is_manually_set",
            side_effect=[True],
        ), patch(
            "streamlit.web.server.server_util.config.get_option",
            side_effect=[True, "browser.server.address"],
        ):
            self.assertTrue(
                server_util.is_url_from_allowed_origins("browser.server.address")
            )