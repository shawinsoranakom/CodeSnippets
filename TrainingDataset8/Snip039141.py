def test_uncaught_exception_no_details(self, mock_st_error, mock_st_exception):
        """If client.showErrorDetails is false, uncaught app errors are logged,
        and a generic error message is printed to the frontend."""
        with testutil.patch_config_options({"client.showErrorDetails": False}):
            exc = RuntimeError("boom!")
            handle_uncaught_app_exception(exc)

            mock_st_error.assert_not_called()
            mock_st_exception.assert_called_once()