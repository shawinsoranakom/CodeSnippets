def test_uncaught_exception_show_details(self, mock_st_error, mock_st_exception):
        """If client.showErrorDetails is true, uncaught app errors print
        to the frontend."""
        with testutil.patch_config_options({"client.showErrorDetails": True}):
            exc = RuntimeError("boom!")
            handle_uncaught_app_exception(exc)

            mock_st_error.assert_not_called()
            mock_st_exception.assert_called_once_with(exc)