def test_run_formatters_handles_oserror_for_black_path(self):
        test_files_path = Path(__file__).parent / "test_files"
        cases = [
            (
                FileNotFoundError,
                str(test_files_path / "nonexistent"),
            ),
            (
                OSError if sys.platform == "win32" else PermissionError,
                str(test_files_path / "black"),
            ),
        ]
        for exception, location in cases:
            with (
                self.subTest(exception.__qualname__),
                AssertFormatterFailureCaughtContext(
                    self, shutil_which_result=location
                ) as ctx,
            ):
                run_formatters([], stderr=ctx.stderr)
                parsed_error = ctx.stderr.getvalue()
                self.assertIn(exception.__qualname__, parsed_error)
                if sys.platform != "win32":
                    self.assertIn(location, parsed_error)