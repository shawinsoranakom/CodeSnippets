def test_failure_to_format_code(self):
        with AssertFormatterFailureCaughtContext(self) as ctx:
            call_command(
                "startapp",
                "mynewapp",
                directory=self.test_dir,
                stdout=ctx.stdout,
                stderr=ctx.stderr,
            )