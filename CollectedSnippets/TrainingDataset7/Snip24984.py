def test_unicode_decode_error(self):
        shutil.copyfile("./not_utf8.sample", "./not_utf8.txt")
        out = StringIO()
        management.call_command("makemessages", locale=[LOCALE], stdout=out)
        self.assertIn(
            "UnicodeDecodeError: skipped file not_utf8.txt in .", out.getvalue()
        )