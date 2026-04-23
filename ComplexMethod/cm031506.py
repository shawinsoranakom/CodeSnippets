def squeeze_current_text(self):
        """Squeeze the text block where the insertion cursor is.

        If the cursor is not in a squeezable block of text, give the
        user a small warning and do nothing.
        """
        # Set tag_name to the first valid tag found on the "insert" cursor.
        tag_names = self.text.tag_names(tk.INSERT)
        for tag_name in ("stdout", "stderr"):
            if tag_name in tag_names:
                break
        else:
            # The insert cursor doesn't have a "stdout" or "stderr" tag.
            self.text.bell()
            return "break"

        # Find the range to squeeze.
        start, end = self.text.tag_prevrange(tag_name, tk.INSERT + "+1c")
        s = self.text.get(start, end)

        # If the last char is a newline, remove it from the range.
        if len(s) > 0 and s[-1] == '\n':
            end = self.text.index("%s-1c" % end)
            s = s[:-1]

        # Delete the text.
        self.base_text.delete(start, end)

        # Prepare an ExpandingButton.
        numoflines = self.count_lines(s)
        expandingbutton = ExpandingButton(s, tag_name, numoflines, self)

        # insert the ExpandingButton to the Text
        self.text.window_create(start, window=expandingbutton,
                                padx=3, pady=5)

        # Insert the ExpandingButton to the list of ExpandingButtons,
        # while keeping the list ordered according to the position of
        # the buttons in the Text widget.
        i = len(self.expandingbuttons)
        while i > 0 and self.text.compare(self.expandingbuttons[i-1],
                                          ">", expandingbutton):
            i -= 1
        self.expandingbuttons.insert(i, expandingbutton)

        return "break"