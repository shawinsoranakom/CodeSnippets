def test_clone_test_db_subprocess_mysql_error(self):
        creation = DatabaseCreation(connection)
        mock_subprocess_call = mock.MagicMock()
        mock_subprocess_call.returncode = 0
        # Simulate load in test database cloning raises an error.
        msg = "Some error"
        mock_subprocess_call_error = mock.MagicMock()
        mock_subprocess_call_error.returncode = 3
        mock_subprocess_call_error.stderr = BytesIO(msg.encode())
        with mock.patch.object(subprocess, "Popen") as mocked_popen:
            mocked_popen.return_value.__enter__.side_effect = [
                mock_subprocess_call,  # mysqldump mock
                mock_subprocess_call_error,  # load mock
            ]
            with captured_stderr() as err, self.assertRaises(SystemExit) as cm:
                creation._clone_db("source_db", "target_db")
            self.assertEqual(cm.exception.code, 3)
        self.assertIn(f"Got an error cloning the test database: {msg}", err.getvalue())