def test_no_locale_raises(self):
        msg = (
            "Unable to find a locale path to store translations for file "
            "__init__.py. Make sure the 'locale' directory exists in an app "
            "or LOCALE_PATHS setting is set."
        )
        with self.assertRaisesMessage(management.CommandError, msg):
            management.call_command("makemessages", locale=[LOCALE], verbosity=0)
        # Working files are cleaned up on an error.
        self.assertFalse(os.path.exists("./app_no_locale/test.html.py"))