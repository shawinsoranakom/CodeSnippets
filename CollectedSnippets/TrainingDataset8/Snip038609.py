def test_missing_config(self):
        """Test that we can initialize our config even if the file is missing."""
        with patch("streamlit.config.os.path.exists") as path_exists:
            path_exists.return_value = False
            config.get_config_options()

            self.assertEqual(True, config.get_option("client.caching"))
            self.assertIsNone(config.get_option("theme.font"))