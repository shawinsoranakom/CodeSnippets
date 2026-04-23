def test_faulthandler_enabled(self, mocked_enable):
        with mock.patch("faulthandler.is_enabled", return_value=False):
            DiscoverRunner(enable_faulthandler=True)
            mocked_enable.assert_called()