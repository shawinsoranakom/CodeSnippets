def assertMsgId(self, msgid, haystack, use_quotes=True):
        return self._assertPoKeyword("msgid", msgid, haystack, use_quotes=use_quotes)