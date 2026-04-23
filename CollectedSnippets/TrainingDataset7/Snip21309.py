def test_sqlsequencereset_no_sequences(self):
        out = io.StringIO()
        err = io.StringIO()
        call_command("sqlsequencereset", "empty_models", stdout=out, stderr=err)
        self.assertEqual(out.getvalue(), "")
        self.assertEqual(err.getvalue(), "No sequences found.\n")