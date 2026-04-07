def test_command_style(self):
        out = StringIO()
        management.call_command("dance", style="Jive", stdout=out)
        self.assertIn("I don't feel like dancing Jive.\n", out.getvalue())
        # Passing options as arguments also works (thanks argparse)
        management.call_command("dance", "--style", "Jive", stdout=out)
        self.assertIn("I don't feel like dancing Jive.\n", out.getvalue())