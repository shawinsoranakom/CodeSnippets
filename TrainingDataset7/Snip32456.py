def test_warning_when_clearing_staticdir(self):
        stdout = StringIO()
        self.run_collectstatic()
        with mock.patch("builtins.input", side_effect=self.mock_input(stdout)):
            call_command("collectstatic", interactive=True, clear=True, stdout=stdout)

        output = stdout.getvalue()
        self.assertNotIn(self.overwrite_warning_msg, output)
        self.assertIn(self.delete_warning_msg, output)