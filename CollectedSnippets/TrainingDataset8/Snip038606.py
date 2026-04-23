def test_on_config_parsed(self, config_options, connect_signal):
        """Tests to make sure callback is handled properly based upon
        _config_file_has_been_parsed and connect_signal."""

        mock_callback = MagicMock(return_value=None)

        with patch.object(config, "_config_options", new=config_options), patch.object(
            config._on_config_parsed, "connect"
        ) as patched_connect, patch.object(
            config._on_config_parsed, "disconnect"
        ) as patched_disconnect:
            mock_callback.reset_mock()
            disconnect_callback = config.on_config_parsed(mock_callback, connect_signal)

            if connect_signal:
                patched_connect.assert_called_once()
                mock_callback.assert_not_called()
            elif config_options:
                patched_connect.assert_not_called()
                mock_callback.assert_called_once()
            else:
                patched_connect.assert_called_once()
                mock_callback.assert_not_called()

            disconnect_callback()
            patched_disconnect.assert_called_once()