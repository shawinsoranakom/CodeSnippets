def test_help_default_options_with_custom_arguments(self):
        args = ["base_command", "--help"]
        out, err = self.run_manage(args)
        self.assertNoOutput(err)
        expected_options = [
            "-h",
            "--option_a OPTION_A",
            "--option_b OPTION_B",
            "--option_c OPTION_C",
            "--version",
            "-v {0,1,2,3}",
            "--settings SETTINGS",
            "--pythonpath PYTHONPATH",
            "--traceback",
            "--no-color",
            "--force-color",
            "args ...",
        ]
        for option in expected_options:
            self.assertOutput(out, f"[{option}]")
        if PY313:
            self.assertOutput(out, "--option_a, -a OPTION_A")
            self.assertOutput(out, "--option_b, -b OPTION_B")
            self.assertOutput(out, "--option_c, -c OPTION_C")
            self.assertOutput(out, "-v, --verbosity {0,1,2,3}")
        else:
            self.assertOutput(out, "--option_a OPTION_A, -a OPTION_A")
            self.assertOutput(out, "--option_b OPTION_B, -b OPTION_B")
            self.assertOutput(out, "--option_c OPTION_C, -c OPTION_C")
            self.assertOutput(out, "-v {0,1,2,3}, --verbosity {0,1,2,3}")