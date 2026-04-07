def test_update_watches_raises_exceptions(self):
        class TestException(Exception):
            pass

        with mock.patch.object(self.reloader, "_update_watches") as mocked_watches:
            with mock.patch.object(
                self.reloader, "check_server_status"
            ) as mocked_server_status:
                mocked_watches.side_effect = TestException()
                mocked_server_status.return_value = True
                with self.assertRaises(TestException):
                    self.reloader.update_watches()
                self.assertIsInstance(
                    mocked_server_status.call_args[0][0], TestException
                )