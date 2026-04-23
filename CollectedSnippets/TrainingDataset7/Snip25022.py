def test_keep_pot_enabled(self):
        management.call_command(
            "makemessages", locale=[LOCALE], verbosity=0, keep_pot=True
        )
        self.assertTrue(os.path.exists(self.POT_FILE))