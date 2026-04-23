def test_subparser_dest_args(self):
        out = StringIO()
        management.call_command("subparser_dest", "foo", bar=12, stdout=out)
        self.assertIn("bar", out.getvalue())