def test_warning_when_overwriting_files_in_staticdir(self):
        stdout = StringIO()
        self.run_collectstatic()
        with mock.patch("builtins.input", side_effect=self.mock_input(stdout)):
            call_command("collectstatic", interactive=True, stdout=stdout)
        output = stdout.getvalue()
        self.assertIn(self.overwrite_warning_msg, output)
        self.assertNotIn(self.delete_warning_msg, output)