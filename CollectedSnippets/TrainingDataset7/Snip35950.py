def test_command_add_arguments_after_common_arguments(self):
        out = StringIO()
        management.call_command("common_args", stdout=out)
        self.assertIn("Detected that --version already exists", out.getvalue())