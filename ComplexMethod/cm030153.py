def setup(self, f, tb):
        self.forget()
        self.stack, self.curindex = self.get_stack(f, tb)
        while tb:
            # when setting up post-mortem debugging with a traceback, save all
            # the original line numbers to be displayed along the current line
            # numbers (which can be different, e.g. due to finally clauses)
            lineno = lasti2lineno(tb.tb_frame.f_code, tb.tb_lasti)
            self.tb_lineno[tb.tb_frame] = lineno
            tb = tb.tb_next
        self.curframe = self.stack[self.curindex][0]
        self.set_convenience_variable(self.curframe, '_frame', self.curframe)
        if self._current_task:
            self.set_convenience_variable(self.curframe, '_asynctask', self._current_task)
        self._save_initial_file_mtime(self.curframe)

        if self._chained_exceptions:
            self.set_convenience_variable(
                self.curframe,
                '_exception',
                self._chained_exceptions[self._chained_exception_index],
            )

        if self.rcLines:
            self.cmdqueue = [
                line for line in self.rcLines
                if line.strip() and not line.strip().startswith("#")
            ]
            self.rcLines = []