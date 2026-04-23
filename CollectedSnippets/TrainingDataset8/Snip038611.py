def test_load_local_config(self):
        """Test that $CWD/.streamlit/config.toml is read, even
        if ~/.streamlit/config.toml is missing.
        """

        local_config = """
        [theme]
        base = "light"
        textColor = "#FFFFFF"
        """

        local_config_path = os.path.join(os.getcwd(), ".streamlit/config.toml")

        open_patch = patch("streamlit.config.open", mock_open(read_data=local_config))
        # patch streamlit.*.os.* instead of os.* for py35 compat
        makedirs_patch = patch("streamlit.config.os.makedirs")
        makedirs_patch.return_value = True
        pathexists_patch = patch("streamlit.config.os.path.exists")
        pathexists_patch.side_effect = lambda path: path == local_config_path

        with open_patch, makedirs_patch, pathexists_patch:
            config.get_config_options()

            self.assertEqual("#FFFFFF", config.get_option("theme.textColor"))
            self.assertIsNone(config.get_option("theme.font"))