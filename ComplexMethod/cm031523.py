def open(self, event=None, editFile=None):
        flist = self.editwin.flist
        # Save in case parent window is closed (ie, during askopenfile()).
        if flist:
            if not editFile:
                filename = self.askopenfile()
            else:
                filename=editFile
            if filename:
                # If editFile is valid and already open, flist.open will
                # shift focus to its existing window.
                # If the current window exists and is a fresh unnamed,
                # unmodified editor window (not an interpreter shell),
                # pass self.loadfile to flist.open so it will load the file
                # in the current window (if the file is not already open)
                # instead of a new window.
                if (self.editwin and
                        not getattr(self.editwin, 'interp', None) and
                        not self.filename and
                        self.get_saved()):
                    flist.open(filename, self.loadfile)
                else:
                    flist.open(filename)
            else:
                if self.text:
                    self.text.focus_set()
            return "break"

        # Code for use outside IDLE:
        if self.get_saved():
            reply = self.maybesave()
            if reply == "cancel":
                self.text.focus_set()
                return "break"
        if not editFile:
            filename = self.askopenfile()
        else:
            filename=editFile
        if filename:
            self.loadfile(filename)
        else:
            self.text.focus_set()
        return "break"