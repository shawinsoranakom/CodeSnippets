def test_subparser_dest_required_args(self):
        out = StringIO()
        management.call_command(
            "subparser_required", "foo_1", "foo_2", bar=12, stdout=out
        )
        self.assertIn("bar", out.getvalue())