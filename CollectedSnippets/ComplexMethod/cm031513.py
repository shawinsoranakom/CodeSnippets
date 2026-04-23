def keypress_event(self, event):
        if not self.is_active():
            return None
        keysym = event.keysym
        if hasattr(event, "mc_state"):
            state = event.mc_state
        else:
            state = 0
        if keysym != "Tab":
            self.lastkey_was_tab = False
        if (len(keysym) == 1 or keysym in ("underscore", "BackSpace")
            or (self.mode == FILES and keysym in
                ("period", "minus"))) \
           and not (state & ~MC_SHIFT):
            # Normal editing of text
            if len(keysym) == 1:
                self._change_start(self.start + keysym)
            elif keysym == "underscore":
                self._change_start(self.start + '_')
            elif keysym == "period":
                self._change_start(self.start + '.')
            elif keysym == "minus":
                self._change_start(self.start + '-')
            else:
                # keysym == "BackSpace"
                if len(self.start) == 0:
                    self.hide_window()
                    return None
                self._change_start(self.start[:-1])
            self.lasttypedstart = self.start
            self.listbox.select_clear(0, int(self.listbox.curselection()[0]))
            self.listbox.select_set(self._binary_search(self.start))
            self._selection_changed()
            return "break"

        elif keysym == "Return":
            self.complete()
            self.hide_window()
            return 'break'

        elif (self.mode == ATTRS and keysym in
              ("period", "space", "parenleft", "parenright", "bracketleft",
               "bracketright")) or \
             (self.mode == FILES and keysym in
              ("slash", "backslash", "quotedbl", "apostrophe")) \
             and not (state & ~MC_SHIFT):
            # If start is a prefix of the selection, but is not '' when
            # completing file names, put the whole
            # selected completion. Anyway, close the list.
            cursel = int(self.listbox.curselection()[0])
            if self.completions[cursel][:len(self.start)] == self.start \
               and (self.mode == ATTRS or self.start):
                self._change_start(self.completions[cursel])
            self.hide_window()
            return None

        elif keysym in ("Home", "End", "Prior", "Next", "Up", "Down") and \
             not state:
            # Move the selection in the listbox
            self.userwantswindow = True
            cursel = int(self.listbox.curselection()[0])
            if keysym == "Home":
                newsel = 0
            elif keysym == "End":
                newsel = len(self.completions)-1
            elif keysym in ("Prior", "Next"):
                jump = self.listbox.nearest(self.listbox.winfo_height()) - \
                       self.listbox.nearest(0)
                if keysym == "Prior":
                    newsel = max(0, cursel-jump)
                else:
                    assert keysym == "Next"
                    newsel = min(len(self.completions)-1, cursel+jump)
            elif keysym == "Up":
                newsel = max(0, cursel-1)
            else:
                assert keysym == "Down"
                newsel = min(len(self.completions)-1, cursel+1)
            self.listbox.select_clear(cursel)
            self.listbox.select_set(newsel)
            self._selection_changed()
            self._change_start(self.completions[newsel])
            return "break"

        elif (keysym == "Tab" and not state):
            if self.lastkey_was_tab:
                # two tabs in a row; insert current selection and close acw
                cursel = int(self.listbox.curselection()[0])
                self._change_start(self.completions[cursel])
                self.hide_window()
                return "break"
            else:
                # first tab; let AutoComplete handle the completion
                self.userwantswindow = True
                self.lastkey_was_tab = True
                return None

        elif any(s in keysym for s in ("Shift", "Control", "Alt",
                                       "Meta", "Command", "Option")):
            # A modifier key, so ignore
            return None

        elif event.char and event.char >= ' ':
            # Regular character with a non-length-1 keycode
            self._change_start(self.start + event.char)
            self.lasttypedstart = self.start
            self.listbox.select_clear(0, int(self.listbox.curselection()[0]))
            self.listbox.select_set(self._binary_search(self.start))
            self._selection_changed()
            return "break"

        else:
            # Unknown event, close the window and let it through.
            self.hide_window()
            return None