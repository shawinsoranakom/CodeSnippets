def test_faulthandler_enabled_fileno(self, mocked_enable):
        # sys.stderr that is not an actual file.
        with (
            mock.patch("faulthandler.is_enabled", return_value=False),
            captured_stderr(),
        ):
            DiscoverRunner(enable_faulthandler=True)
            mocked_enable.assert_called()