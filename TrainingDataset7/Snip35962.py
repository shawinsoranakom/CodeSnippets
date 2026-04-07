def test_outputwrapper_flush(self):
        out = StringIO()
        with mock.patch.object(out, "flush") as mocked_flush:
            management.call_command("outputwrapper", stdout=out)
        self.assertIn("Working...", out.getvalue())
        self.assertIs(mocked_flush.called, True)