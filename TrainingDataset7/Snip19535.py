def test_silenced_error(self):
        out = StringIO()
        err = StringIO()
        call_command("check", stdout=out, stderr=err)
        self.assertEqual(
            out.getvalue(), "System check identified no issues (1 silenced).\n"
        )
        self.assertEqual(err.getvalue(), "")