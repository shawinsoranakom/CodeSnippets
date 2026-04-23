def _insert_printable_char(self, ch):
        self._update_max_yx()
        (y, x) = self.win.getyx()
        backyx = None
        while y < self.maxy or x < self.maxx:
            if self.insert_mode:
                oldch = self.win.inch()
            # The try-catch ignores the error we trigger from some curses
            # versions by trying to write into the lowest-rightmost spot
            # in the window.
            try:
                self.win.addch(ch)
            except curses.error:
                pass
            if not self.insert_mode or not curses.ascii.isprint(oldch):
                break
            ch = oldch
            (y, x) = self.win.getyx()
            # Remember where to put the cursor back since we are in insert_mode
            if backyx is None:
                backyx = y, x

        if backyx is not None:
            self.win.move(*backyx)