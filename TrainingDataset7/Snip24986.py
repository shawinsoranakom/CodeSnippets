def test_extraction_warning(self):
        """
        test xgettext warning about multiple bare interpolation placeholders
        """
        shutil.copyfile("./code.sample", "./code_sample.py")
        out = StringIO()
        management.call_command("makemessages", locale=[LOCALE], stdout=out)
        self.assertIn("code_sample.py:4", out.getvalue())