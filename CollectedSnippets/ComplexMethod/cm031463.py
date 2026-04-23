def get_surrounding_brackets(self, openers='([{', mustclose=False):
        """Return bracket indexes or None.

        If the index given to the HyperParser is surrounded by a
        bracket defined in openers (or at least has one before it),
        return the indices of the opening bracket and the closing
        bracket (or the end of line, whichever comes first).

        If it is not surrounded by brackets, or the end of line comes
        before the closing bracket and mustclose is True, returns None.
        """

        bracketinglevel = self.bracketing[self.indexbracket][1]
        before = self.indexbracket
        while (not self.isopener[before] or
              self.rawtext[self.bracketing[before][0]] not in openers or
              self.bracketing[before][1] > bracketinglevel):
            before -= 1
            if before < 0:
                return None
            bracketinglevel = min(bracketinglevel, self.bracketing[before][1])
        after = self.indexbracket + 1
        while (after < len(self.bracketing) and
              self.bracketing[after][1] >= bracketinglevel):
            after += 1

        beforeindex = self.text.index("%s-%dc" %
            (self.stopatindex, len(self.rawtext)-self.bracketing[before][0]))
        if (after >= len(self.bracketing) or
           self.bracketing[after][0] > len(self.rawtext)):
            if mustclose:
                return None
            afterindex = self.stopatindex
        else:
            # We are after a real char, so it is a ')' and we give the
            # index before it.
            afterindex = self.text.index(
                "%s-%dc" % (self.stopatindex,
                 len(self.rawtext)-(self.bracketing[after][0]-1)))

        return beforeindex, afterindex