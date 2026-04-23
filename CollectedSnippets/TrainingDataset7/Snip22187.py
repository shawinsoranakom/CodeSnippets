def test_exclude_option_errors(self):
        """Excluding a bogus app or model should raise an error."""
        msg = "No installed app with label 'foo_app'."
        with self.assertRaisesMessage(management.CommandError, msg):
            management.call_command(
                "loaddata", "fixture1", exclude=["foo_app"], verbosity=0
            )

        msg = "Unknown model: fixtures.FooModel"
        with self.assertRaisesMessage(management.CommandError, msg):
            management.call_command(
                "loaddata", "fixture1", exclude=["fixtures.FooModel"], verbosity=0
            )