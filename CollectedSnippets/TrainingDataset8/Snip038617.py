def test_config_options_warn_on_server_change(self, get_logger):
        """Test that a warning is logged if a user changes a config file in the
        server section."""

        global_config_path = "/mock/home/folder/.streamlit/config.toml"
        makedirs_patch = patch("streamlit.config.os.makedirs")
        makedirs_patch.return_value = True
        pathexists_patch = patch("streamlit.config.os.path.exists")
        pathexists_patch.side_effect = lambda path: path == global_config_path
        mock_logger = get_logger()

        global_config = """
        [server]
        address = "localhost"
        """
        open_patch = patch("streamlit.config.open", mock_open(read_data=global_config))

        with open_patch, makedirs_patch, pathexists_patch:
            config.get_config_options()

        global_config = """
        [server]
        address = "streamlit.io"
        """
        open_patch = patch("streamlit.config.open", mock_open(read_data=global_config))

        with open_patch, makedirs_patch, pathexists_patch:
            config.get_config_options(force_reparse=True)

        mock_logger.warning.assert_any_call(
            "An update to the [server] config option section was detected."
            " To have these changes be reflected, please restart streamlit."
        )