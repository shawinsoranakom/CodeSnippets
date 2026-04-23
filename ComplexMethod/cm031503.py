def find_again(self, text):
        """Repeat the last search.

        If no search was previously run, open a new search dialog.  In
        this case, no search is done.

        If a search was previously run, the search dialog won't be
        shown and the options from the previous search (including the
        search pattern) will be used to find the next occurrence
        of the pattern.  Next is relative based on direction.

        Position the window to display the located occurrence in the
        text.

        Return True if the search was successful and False otherwise.
        """
        if not self.engine.getpat():
            self.open(text)
            return False
        if not self.engine.getprog():
            return False
        res = self.engine.search_text(text)
        if res:
            line, m = res
            i, j = m.span()
            first = "%d.%d" % (line, i)
            last = "%d.%d" % (line, j)
            try:
                selfirst = text.index("sel.first")
                sellast = text.index("sel.last")
                if selfirst == first and sellast == last:
                    self.bell()
                    return False
            except TclError:
                pass
            text.tag_remove("sel", "1.0", "end")
            text.tag_add("sel", first, last)
            text.mark_set("insert", self.engine.isback() and first or last)
            text.see("insert")
            return True
        else:
            self.bell()
            return False