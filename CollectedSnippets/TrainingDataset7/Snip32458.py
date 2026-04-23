def test_no_warning_when_staticdir_does_not_exist(self):
        stdout = StringIO()
        shutil.rmtree(settings.STATIC_ROOT)
        call_command("collectstatic", interactive=True, stdout=stdout)
        output = stdout.getvalue()
        self.assertNotIn(self.overwrite_warning_msg, output)
        self.assertNotIn(self.delete_warning_msg, output)
        self.assertIn(self.files_copied_msg, output)