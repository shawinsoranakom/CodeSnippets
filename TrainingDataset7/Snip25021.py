def test_keep_pot_explicitly_disabled(self):
        management.call_command(
            "makemessages", locale=[LOCALE], verbosity=0, keep_pot=False
        )
        self.assertFalse(os.path.exists(self.POT_FILE))