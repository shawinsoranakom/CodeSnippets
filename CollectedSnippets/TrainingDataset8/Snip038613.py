def test_load_global_local_flag_config(self):
        """Test that CLI flags have higher priority than both
        ~/.streamlit/config.toml and $CWD/.streamlit/config.toml at parse time.
        """

        global_config = """
        [theme]
        base = "dark"
        font = "sans serif"
        textColor = "#FFFFFF"
        """

        local_config = """
        [theme]
        base = "light"
        font = "serif"
        """

        global_config_path = "/mock/home/folder/.streamlit/config.toml"
        local_config_path = os.path.join(os.getcwd(), ".streamlit/config.toml")

        global_open = mock_open(read_data=global_config)
        local_open = mock_open(read_data=local_config)
        open = mock_open()
        open.side_effect = [global_open.return_value, local_open.return_value]

        open_patch = patch("streamlit.config.open", open)
        # patch streamlit.*.os.* instead of os.* for py35 compat
        makedirs_patch = patch("streamlit.config.os.makedirs")
        makedirs_patch.return_value = True
        pathexists_patch = patch("streamlit.config.os.path.exists")
        pathexists_patch.side_effect = lambda path: path in [
            global_config_path,
            local_config_path,
        ]

        with open_patch, makedirs_patch, pathexists_patch:
            config.get_config_options(options_from_flags={"theme.font": "monospace"})

            self.assertEqual("light", config.get_option("theme.base"))
            self.assertEqual("#FFFFFF", config.get_option("theme.textColor"))
            self.assertEqual("monospace", config.get_option("theme.font"))