def test_ambigious_prefix(self):
        msg = (
            "More than one migration matches 'a' in app 'migrations'. Please "
            "be more specific."
        )
        with self.assertRaisesMessage(CommandError, msg):
            call_command("optimizemigration", "migrations", "a")