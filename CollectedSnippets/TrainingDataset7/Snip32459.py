def test_no_warning_for_empty_staticdir(self):
        stdout = StringIO()
        with tempfile.TemporaryDirectory(
            prefix="collectstatic_empty_staticdir_test"
        ) as static_dir:
            with override_settings(STATIC_ROOT=static_dir):
                call_command("collectstatic", interactive=True, stdout=stdout)
        output = stdout.getvalue()
        self.assertNotIn(self.overwrite_warning_msg, output)
        self.assertNotIn(self.delete_warning_msg, output)
        self.assertIn(self.files_copied_msg, output)