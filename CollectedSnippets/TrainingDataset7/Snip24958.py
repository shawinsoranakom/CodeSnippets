def assertMsgStr(self, msgstr, haystack, use_quotes=True):
        return self._assertPoKeyword("msgstr", msgstr, haystack, use_quotes=use_quotes)