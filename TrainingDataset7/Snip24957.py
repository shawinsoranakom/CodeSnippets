def assertMsgIdPlural(self, msgid, haystack, use_quotes=True):
        return self._assertPoKeyword(
            "msgid_plural", msgid, haystack, use_quotes=use_quotes
        )