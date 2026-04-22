def test_install_config_watcher(
        self, patched_watch_file, patched_get_config_options
    ):
        with patch("os.path.exists", return_value=True):
            bootstrap._install_config_watchers(flag_options={"server_port": 8502})
        self.assertEqual(patched_watch_file.call_count, 2)

        args, _kwargs = patched_watch_file.call_args_list[0]
        on_config_changed = args[1]

        # Simulate a config file change being detected.
        on_config_changed("/unused/nonexistent/file/path")

        patched_get_config_options.assert_called_once_with(
            force_reparse=True,
            options_from_flags={
                "server.port": 8502,
            },
        )