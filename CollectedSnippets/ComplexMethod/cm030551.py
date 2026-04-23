def trace(self, frame, event, arg):
        if self.done:
            return
        assert lineno_matches_lasti(frame)
        # frame.f_code.co_firstlineno is the first line of the decorator when
        # 'function' is decorated and the decorator may be written using
        # multiple physical lines when it is too long. Use the first line
        # trace event in 'function' to find the first line of 'function'.
        if (self.firstLine is None and frame.f_code == self.code and
                event == 'line'):
            self.firstLine = frame.f_lineno - 1
        if (event == self.event and self.firstLine is not None and
                frame.f_lineno == self.firstLine + self.jumpFrom):
            f = frame
            while f is not None and f.f_code != self.code:
                f = f.f_back
            if f is not None:
                # Cope with non-integer self.jumpTo (because of
                # no_jump_to_non_integers below).
                try:
                    frame.f_lineno = self.firstLine + self.jumpTo
                except TypeError:
                    frame.f_lineno = self.jumpTo
                self.done = True
        return self.trace