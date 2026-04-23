def open_completions(self, args):
        """Find the completions and create the AutoCompleteWindow.
        Return True if successful (no syntax error or so found).
        If complete is True, then if there's nothing to complete and no
        start of completion, won't open completions and return False.
        If mode is given, will open a completion list only in this mode.
        """
        evalfuncs, complete, wantwin, mode = args
        # Cancel another delayed call, if it exists.
        if self._delayed_completion_id is not None:
            self.text.after_cancel(self._delayed_completion_id)
            self._delayed_completion_id = None

        hp = HyperParser(self.editwin, "insert")
        curline = self.text.get("insert linestart", "insert")
        i = j = len(curline)
        if hp.is_in_string() and (not mode or mode==FILES):
            # Find the beginning of the string.
            # fetch_completions will look at the file system to determine
            # whether the string value constitutes an actual file name
            # XXX could consider raw strings here and unescape the string
            # value if it's not raw.
            self._remove_autocomplete_window()
            mode = FILES
            # Find last separator or string start
            while i and curline[i-1] not in "'\"" + SEPS:
                i -= 1
            comp_start = curline[i:j]
            j = i
            # Find string start
            while i and curline[i-1] not in "'\"":
                i -= 1
            comp_what = curline[i:j]
        elif hp.is_in_code() and (not mode or mode==ATTRS):
            self._remove_autocomplete_window()
            mode = ATTRS
            while i and (curline[i-1] in ID_CHARS or ord(curline[i-1]) > 127):
                i -= 1
            comp_start = curline[i:j]
            if i and curline[i-1] == '.':  # Need object with attributes.
                hp.set_index("insert-%dc" % (len(curline)-(i-1)))
                comp_what = hp.get_expression()
                if (not comp_what or
                   (not evalfuncs and comp_what.find('(') != -1)):
                    return None
            else:
                comp_what = ""
        else:
            return None

        if complete and not comp_what and not comp_start:
            return None
        comp_lists = self.fetch_completions(comp_what, mode)
        if not comp_lists[0]:
            return None
        self.autocompletewindow = self._make_autocomplete_window()
        return not self.autocompletewindow.show_window(
                comp_lists, "insert-%dc" % len(comp_start),
                complete, mode, wantwin)