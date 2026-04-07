def test_call_command_option_parsing(self):
        """
        When passing the long option name to call_command, the available option
        key is the option dest name (#22985).
        """
        out = StringIO()
        management.call_command("dance", stdout=out, opt_3=True)
        self.assertIn("option3", out.getvalue())
        self.assertNotIn("opt_3", out.getvalue())
        self.assertNotIn("opt-3", out.getvalue())