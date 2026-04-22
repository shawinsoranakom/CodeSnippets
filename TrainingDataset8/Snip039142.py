def test_handle_print_rich_exception(self):
        """Test if the print rich exception method is working fine."""

        with io.StringIO() as buf:
            # Capture stdout logs (rich logs to stdout)
            with contextlib.redirect_stdout(buf):
                _print_rich_exception(Exception("boom!"))
            # Capture the stdout output
            captured_output = buf.getvalue()

            assert "Exception:" in captured_output
            assert "boom!" in captured_output