def test_load_global_config(self):
        """Test that ~/.streamlit/config.toml is read."""
        global_config = """
        [theme]
        base = "dark"
        font = "sans serif"
        """
        global_config_path = "/mock/home/folder/.streamlit/config.toml"

        open_patch = patch("streamlit.config.open", mock_open(read_data=global_config))
        # patch streamlit.*.os.* instead of os.* for py35 compat
        makedirs_patch = patch("streamlit.config.os.makedirs")
        makedirs_patch.return_value = True
        pathexists_patch = patch("streamlit.config.os.path.exists")
        pathexists_patch.side_effect = lambda path: path == global_config_path

        with open_patch, makedirs_patch, pathexists_patch:
            config.get_config_options()

            self.assertEqual("sans serif", config.get_option("theme.font"))
            self.assertIsNone(config.get_option("theme.textColor"))