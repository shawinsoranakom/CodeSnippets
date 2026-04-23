def test_call_command_unrecognized_option(self):
        msg = (
            "Unknown option(s) for dance command: unrecognized. Valid options "
            "are: example, force_color, help, integer, no_color, opt_3, "
            "option3, pythonpath, settings, skip_checks, stderr, stdout, "
            "style, traceback, verbosity, version."
        )
        with self.assertRaisesMessage(TypeError, msg):
            management.call_command("dance", unrecognized=1)

        msg = (
            "Unknown option(s) for dance command: unrecognized, unrecognized2. "
            "Valid options are: example, force_color, help, integer, no_color, "
            "opt_3, option3, pythonpath, settings, skip_checks, stderr, "
            "stdout, style, traceback, verbosity, version."
        )
        with self.assertRaisesMessage(TypeError, msg):
            management.call_command("dance", unrecognized=1, unrecognized2=1)