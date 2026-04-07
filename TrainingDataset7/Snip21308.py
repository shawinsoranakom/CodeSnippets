def test_sqlflush_no_tables(self):
        out = io.StringIO()
        err = io.StringIO()
        call_command("sqlflush", stdout=out, stderr=err)
        self.assertEqual(out.getvalue(), "")
        self.assertEqual(err.getvalue(), "No tables found.\n")