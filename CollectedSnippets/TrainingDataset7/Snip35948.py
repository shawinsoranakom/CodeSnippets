def test_call_command_with_required_parameters_in_options(self):
        out = StringIO()
        management.call_command(
            "required_option", need_me="foo", needme2="bar", stdout=out
        )
        self.assertIn("need_me", out.getvalue())
        self.assertIn("needme2", out.getvalue())