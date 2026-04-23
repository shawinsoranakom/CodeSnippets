def test_createcachetable_dry_run_mode(self):
        out = io.StringIO()
        management.call_command("createcachetable", dry_run=True, stdout=out)
        output = out.getvalue()
        self.assertTrue(output.startswith("CREATE TABLE"))