def test_keep_pot_disabled_by_default(self):
        management.call_command("makemessages", locale=[LOCALE], verbosity=0)
        self.assertFalse(os.path.exists(self.POT_FILE))