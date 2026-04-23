def test_prune_no_app_label(self):
        msg = "Migrations can be pruned only when an app is specified."
        with self.assertRaisesMessage(CommandError, msg):
            call_command("migrate", prune=True)