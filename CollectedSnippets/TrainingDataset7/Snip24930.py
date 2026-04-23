def test_no_compile_when_unneeded(self):
        mo_file_en = Path(self.MO_FILE_EN)
        mo_file_en.touch()
        stdout = StringIO()
        call_command("compilemessages", locale=["en"], stdout=stdout, verbosity=1)
        msg = "%s” is already compiled and up to date." % mo_file_en.with_suffix(".po")
        self.assertIn(msg, stdout.getvalue())