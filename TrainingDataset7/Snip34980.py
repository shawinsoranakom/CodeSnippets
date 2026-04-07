def test_faulthandler_disabled(self, mocked_enable):
        with mock.patch("faulthandler.is_enabled", return_value=False):
            DiscoverRunner(enable_faulthandler=False)
            mocked_enable.assert_not_called()