def test_multi_database_init_connection_state_called_once(self):
        for db in self.databases:
            with self.subTest(database=db):
                with patch.object(connections[db], "commit", return_value=None):
                    with patch.object(
                        connections[db],
                        "check_database_version_supported",
                    ) as mocked_check_database_version_supported:
                        connections[db].init_connection_state()
                        after_first_calls = len(
                            mocked_check_database_version_supported.mock_calls
                        )
                        connections[db].init_connection_state()
                        self.assertEqual(
                            len(mocked_check_database_version_supported.mock_calls),
                            after_first_calls,
                        )