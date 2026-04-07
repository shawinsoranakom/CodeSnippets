def test_faulthandler_already_enabled(self, mocked_enable):
        with mock.patch("faulthandler.is_enabled", return_value=True):
            DiscoverRunner(enable_faulthandler=True)
            mocked_enable.assert_not_called()