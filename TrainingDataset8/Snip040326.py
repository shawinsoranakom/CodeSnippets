def test_rotates_one_port(
        self, patched_server_port_is_manually_set, patched__set_option
    ):
        app = mock.MagicMock()

        patched_server_port_is_manually_set.return_value = False
        with pytest.raises(RetriesExceeded):
            with patch(
                "streamlit.web.server.server.HTTPServer",
                return_value=self.get_httpserver(),
            ):
                start_listening(app)

                PortRotateOneTest.which_port.assert_called_with(8502)

                patched__set_option.assert_called_with(
                    "server.port", 8501, config.ConfigOption.STREAMLIT_DEFINITION
                )