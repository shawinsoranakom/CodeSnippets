def test_safe_status(self):
        """
        Translating a string requiring no auto-escaping with gettext or
        pgettext shouldn't change the "safe" status.
        """
        trans_real._active = Local()
        trans_real._translations = {}
        s1 = mark_safe("Password")
        s2 = mark_safe("May")
        with translation.override("de", deactivate=True):
            self.assertIs(type(gettext(s1)), SafeString)
            self.assertIs(type(pgettext("month name", s2)), SafeString)
        self.assertEqual("aPassword", SafeString("a") + s1)
        self.assertEqual("Passworda", s1 + SafeString("a"))
        self.assertEqual("Passworda", s1 + mark_safe("a"))
        self.assertEqual("aPassword", mark_safe("a") + s1)
        self.assertEqual("as", mark_safe("a") + mark_safe("s"))