def assertGettext(self, msgid, msgstr):
        result = gettext(msgid)
        self.assertIn(
            msgstr,
            result,
            "The string '%s' isn't in the translation of '%s'; the actual result is "
            "'%s'." % (msgstr, msgid, result),
        )