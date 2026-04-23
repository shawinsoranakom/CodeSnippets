def test_check_server_status_raises_error(self):
        with mock.patch.object(self.reloader.client, "query") as mocked_query:
            mocked_query.side_effect = Exception()
            with self.assertRaises(autoreload.WatchmanUnavailable):
                self.reloader.check_server_status()