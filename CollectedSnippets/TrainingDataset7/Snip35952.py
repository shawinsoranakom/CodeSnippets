def test_mutually_exclusive_group_required_const_options(self):
        tests = [
            ("append_const", [42]),
            ("const", 31),
            ("count", 1),
            ("flag_false", False),
            ("flag_true", True),
        ]
        for arg, value in tests:
            out = StringIO()
            expected_output = "%s=%s" % (arg, value)
            with self.subTest(arg=arg):
                management.call_command(
                    "mutually_exclusive_required",
                    "--%s" % arg,
                    stdout=out,
                )
                self.assertIn(expected_output, out.getvalue())
                out.truncate(0)
                management.call_command(
                    "mutually_exclusive_required",
                    **{arg: value, "stdout": out},
                )
                self.assertIn(expected_output, out.getvalue())