def test_reload_secrets_when_file_changes(self, mock_watch_file):
        """When secrets.toml is loaded, the secrets file gets watched."""
        with patch("builtins.open", new_callable=mock_open, read_data=MOCK_TOML):
            self.assertEqual("Jane", self.secrets["db_username"])
            self.assertEqual("12345qwerty", self.secrets["db_password"])
            self.assertEqual("Jane", os.environ["db_username"])
            self.assertEqual("12345qwerty", os.environ["db_password"])

        # watch_file should have been called on the "secrets.toml" file with
        # the "poll" watcher_type. ("poll" is used here - rather than whatever
        # is set in config - because Streamlit Cloud loads secrets.toml from
        # a virtual filesystem that watchdog is unable to fire events for.)
        mock_watch_file.assert_called_once_with(
            MOCK_SECRETS_FILE_LOC,
            self.secrets._on_secrets_file_changed,
            watcher_type="poll",
        )

        # Mock the `send` method to later verify that it has been called.
        self.secrets._file_change_listener.send = MagicMock()

        # Change the text that will be loaded on the next call to `open`
        new_mock_toml = "db_username='Joan'"
        with patch("builtins.open", new_callable=mock_open, read_data=new_mock_toml):
            # Trigger a secrets file reload, ensure the secrets dict
            # gets repopulated as expected, and ensure that os.environ is
            # also updated properly.
            self.secrets._on_secrets_file_changed(MOCK_SECRETS_FILE_LOC)

            # A change in `secrets.toml` should emit a signal.
            self.secrets._file_change_listener.send.assert_called_once()

            self.assertEqual("Joan", self.secrets["db_username"])
            self.assertIsNone(self.secrets.get("db_password"))
            self.assertEqual("Joan", os.environ["db_username"])
            self.assertIsNone(os.environ.get("db_password"))