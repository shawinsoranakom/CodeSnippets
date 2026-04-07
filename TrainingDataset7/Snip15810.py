def test_specific_help(self):
        "--help can be used on a specific command"
        args = ["check", "--help"]
        out, err = self.run_manage(args)
        self.assertNoOutput(err)
        # Command-specific options like --tag appear before options common to
        # all commands like --version.
        tag_location = out.find("--tag")
        version_location = out.find("--version")
        self.assertNotEqual(tag_location, -1)
        self.assertNotEqual(version_location, -1)
        self.assertLess(tag_location, version_location)
        self.assertOutput(
            out, "Checks the entire Django project for potential problems."
        )