def test_is_url_from_allowed_origins_CORS_off(self):
        with patch(
            "streamlit.web.server.server_util.config.get_option", side_effect=[False]
        ):
            self.assertTrue(server_util.is_url_from_allowed_origins("does not matter"))