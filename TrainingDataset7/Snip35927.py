def test_command(self):
        out = StringIO()
        management.call_command("dance", stdout=out)
        self.assertIn("I don't feel like dancing Rock'n'Roll.\n", out.getvalue())