def replace_all(self, event=None):
        """Handle the Replace All button.

        Search text for occurrences of the Find value and replace
        each of them.  The 'wrap around' value controls the start
        point for searching.  If wrap isn't set, then the searching
        starts at the first occurrence after the current selection;
        if wrap is set, the replacement starts at the first line.
        The replacement is always done top-to-bottom in the text.
        """
        prog = self.engine.getprog()
        if not prog:
            return
        repl = self.replvar.get()
        text = self.text
        res = self.engine.search_text(text, prog)
        if not res:
            self.bell()
            return
        text.tag_remove("sel", "1.0", "end")
        text.tag_remove("hit", "1.0", "end")
        line = res[0]
        col = res[1].start()
        if self.engine.iswrap():
            line = 1
            col = 0
        ok = True
        first = last = None
        # XXX ought to replace circular instead of top-to-bottom when wrapping
        text.undo_block_start()
        while res := self.engine.search_forward(
                text, prog, line, col, wrap=False, ok=ok):
            line, m = res
            chars = text.get("%d.0" % line, "%d.0" % (line+1))
            orig = m.group()
            new = self._replace_expand(m, repl)
            if new is None:
                break
            i, j = m.span()
            first = "%d.%d" % (line, i)
            last = "%d.%d" % (line, j)
            if new == orig:
                text.mark_set("insert", last)
            else:
                text.mark_set("insert", first)
                if first != last:
                    text.delete(first, last)
                if new:
                    text.insert(first, new, self.insert_tags)
            col = i + len(new)
            ok = False
        text.undo_block_stop()
        if first and last:
            self.show_hit(first, last)
        self.close()