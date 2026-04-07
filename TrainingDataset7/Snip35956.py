def test_required_const_options(self):
        args = {
            "append_const": [42],
            "const": 31,
            "count": 1,
            "flag_false": False,
            "flag_true": True,
        }
        expected_output = "\n".join(
            "%s=%s" % (arg, value) for arg, value in args.items()
        )
        out = StringIO()
        management.call_command(
            "required_constant_option",
            "--append_const",
            "--const",
            "--count",
            "--flag_false",
            "--flag_true",
            stdout=out,
        )
        self.assertIn(expected_output, out.getvalue())
        out.truncate(0)
        management.call_command("required_constant_option", **args, stdout=out)
        self.assertIn(expected_output, out.getvalue())