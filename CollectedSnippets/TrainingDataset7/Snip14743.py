def ngettext(self, msgid1, msgid2, n):
        try:
            tmsg = self._catalog.plural(msgid1, n)
        except KeyError:
            if self._fallback:
                return self._fallback.ngettext(msgid1, msgid2, n)
            if n == 1:
                tmsg = msgid1
            else:
                tmsg = msgid2
        return tmsg