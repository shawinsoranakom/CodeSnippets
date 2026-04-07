def test_mutually_exclusive_group_required_options(self):
        out = StringIO()
        management.call_command("mutually_exclusive_required", foo_id=1, stdout=out)
        self.assertIn("foo_id", out.getvalue())
        management.call_command(
            "mutually_exclusive_required", foo_name="foo", stdout=out
        )
        self.assertIn("foo_name", out.getvalue())
        msg = (
            "Error: one of the arguments --foo-id --foo-name --foo-list "
            "--append_const --const --count --flag_false --flag_true is "
            "required"
        )
        with self.assertRaisesMessage(CommandError, msg):
            management.call_command("mutually_exclusive_required", stdout=out)