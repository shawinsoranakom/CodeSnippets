def enter_callback(self, event):
        if self.executing and not self.reading:
            return # Let the default binding (insert '\n') take over
        # If some text is selected, recall the selection
        # (but only if this before the I/O mark)
        try:
            sel = self.text.get("sel.first", "sel.last")
            if sel:
                if self.text.compare("sel.last", "<=", "iomark"):
                    self.recall(sel, event)
                    return "break"
        except:
            pass
        # If we're strictly before the line containing iomark, recall
        # the current line, less a leading prompt, less leading or
        # trailing whitespace
        if self.text.compare("insert", "<", "iomark linestart"):
            # Check if there's a relevant stdin range -- if so, use it.
            # Note: "stdin" blocks may include several successive statements,
            # so look for "console" tags on the newline before each statement
            # (and possibly on prompts).
            prev = self.text.tag_prevrange("stdin", "insert")
            if (
                    prev and
                    self.text.compare("insert", "<", prev[1]) and
                    # The following is needed to handle empty statements.
                    "console" not in self.text.tag_names("insert")
            ):
                prev_cons = self.text.tag_prevrange("console", "insert")
                if prev_cons and self.text.compare(prev_cons[1], ">=", prev[0]):
                    prev = (prev_cons[1], prev[1])
                next_cons = self.text.tag_nextrange("console", "insert")
                if next_cons and self.text.compare(next_cons[0], "<", prev[1]):
                    prev = (prev[0], self.text.index(next_cons[0] + "+1c"))
                self.recall(self.text.get(prev[0], prev[1]), event)
                return "break"
            next = self.text.tag_nextrange("stdin", "insert")
            if next and self.text.compare("insert lineend", ">=", next[0]):
                next_cons = self.text.tag_nextrange("console", "insert lineend")
                if next_cons and self.text.compare(next_cons[0], "<", next[1]):
                    next = (next[0], self.text.index(next_cons[0] + "+1c"))
                self.recall(self.text.get(next[0], next[1]), event)
                return "break"
            # No stdin mark -- just get the current line, less any prompt
            indices = self.text.tag_nextrange("console", "insert linestart")
            if indices and \
               self.text.compare(indices[0], "<=", "insert linestart"):
                self.recall(self.text.get(indices[1], "insert lineend"), event)
            else:
                self.recall(self.text.get("insert linestart", "insert lineend"), event)
            return "break"
        # If we're between the beginning of the line and the iomark, i.e.
        # in the prompt area, move to the end of the prompt
        if self.text.compare("insert", "<", "iomark"):
            self.text.mark_set("insert", "iomark")
        # If we're in the current input and there's only whitespace
        # beyond the cursor, erase that whitespace first
        s = self.text.get("insert", "end-1c")
        if s and not s.strip():
            self.text.delete("insert", "end-1c")
        # If we're in the current input before its last line,
        # insert a newline right at the insert point
        if self.text.compare("insert", "<", "end-1c linestart"):
            self.newline_and_indent_event(event)
            return "break"
        # We're in the last line; append a newline and submit it
        self.text.mark_set("insert", "end-1c")
        if self.reading:
            self.text.insert("insert", "\n")
            self.text.see("insert")
        else:
            self.newline_and_indent_event(event)
        self.text.update_idletasks()
        if self.reading:
            self.top.quit() # Break out of recursive mainloop()
        else:
            self.runit()
        return "break"