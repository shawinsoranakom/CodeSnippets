def test_clone_test_db_subprocess_mysqldump_error(self):
        creation = DatabaseCreation(connection)
        mock_subprocess_call = mock.MagicMock()
        mock_subprocess_call.returncode = 0
        # Simulate mysqldump in test database cloning raises an error.
        msg = "Couldn't execute 'SELECT ...'"
        mock_subprocess_call_error = mock.MagicMock()
        mock_subprocess_call_error.returncode = 2
        mock_subprocess_call_error.stderr = BytesIO(msg.encode())
        with mock.patch.object(subprocess, "Popen") as mocked_popen:
            mocked_popen.return_value.__enter__.side_effect = [
                mock_subprocess_call_error,  # mysqldump mock
                mock_subprocess_call,  # load mock
            ]
            with captured_stderr() as err, self.assertRaises(SystemExit) as cm:
                creation._clone_db("source_db", "target_db")
            self.assertEqual(cm.exception.code, 2)
        self.assertIn(
            f"Got an error on mysqldump when cloning the test database: {msg}",
            err.getvalue(),
        )