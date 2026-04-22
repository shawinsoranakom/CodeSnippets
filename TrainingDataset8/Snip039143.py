def test_handle_uncaught_app_exception_with_rich(self):
        """Test if the exception is logged with rich enabled and disabled."""
        exc = Exception("boom!")
        with testutil.patch_config_options({"logger.enableRich": True}):
            with io.StringIO() as buf:
                # Capture stdout logs (rich logs to stdout)
                with contextlib.redirect_stdout(buf):
                    handle_uncaught_app_exception(exc)
                # Capture the stdout output
                captured_output = buf.getvalue()

                assert "Exception:" in captured_output
                assert "boom!" in captured_output
                # Uncaught app exception is only used by the non-rich exception logging
                assert "Uncaught app exception" not in captured_output
        with testutil.patch_config_options({"logger.enableRich": False}):
            with io.StringIO() as buf:
                # Capture stdout logs
                with contextlib.redirect_stdout(buf):
                    handle_uncaught_app_exception(exc)
                # Capture the stdout output
                captured_output = buf.getvalue()

                # With rich deactivated, the exception is not logged to stdout
                assert "Exception:" not in captured_output
                assert "boom!" not in captured_output