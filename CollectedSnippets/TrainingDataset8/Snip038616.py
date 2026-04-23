def test_config_options_removed_on_reparse(self):
        """Test that config options that are removed in a file are also removed
        from our _config_options dict."""

        global_config_path = "/mock/home/folder/.streamlit/config.toml"
        makedirs_patch = patch("streamlit.config.os.makedirs")
        makedirs_patch.return_value = True
        pathexists_patch = patch("streamlit.config.os.path.exists")
        pathexists_patch.side_effect = lambda path: path == global_config_path

        global_config = """
        [theme]
        base = "dark"
        font = "sans serif"
        """
        open_patch = patch("streamlit.config.open", mock_open(read_data=global_config))

        with open_patch, makedirs_patch, pathexists_patch:
            config.get_config_options()

            self.assertEqual("dark", config.get_option("theme.base"))
            self.assertEqual("sans serif", config.get_option("theme.font"))

        global_config = """
        [theme]
        base = "dark"
        """
        open_patch = patch("streamlit.config.open", mock_open(read_data=global_config))

        with open_patch, makedirs_patch, pathexists_patch:
            config.get_config_options(force_reparse=True)

            self.assertEqual("dark", config.get_option("theme.base"))
            self.assertEqual(None, config.get_option("theme.font"))