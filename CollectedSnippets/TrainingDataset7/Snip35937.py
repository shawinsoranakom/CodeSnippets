def test_calling_a_command_with_only_empty_parameter_should_ends_gracefully(self):
        out = StringIO()
        management.call_command("hal", "--empty", stdout=out)
        self.assertEqual(out.getvalue(), "\nDave, I can't do that.\n")