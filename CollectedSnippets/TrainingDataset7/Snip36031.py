def test_check_errors_called(self, mocked_check_errors):
        fake_method = mock.MagicMock(return_value=None)
        fake_reloader = mock.MagicMock()
        autoreload.start_django(fake_reloader, fake_method)
        self.assertCountEqual(mocked_check_errors.call_args[0], [fake_method])