def test_config_show_command(self):
        """Tests the config show command calls the corresponding method in
        config
        """
        with patch("streamlit.config.show_config") as mock_config:
            self.runner.invoke(cli, ["config", "show"])
            mock_config.assert_called()