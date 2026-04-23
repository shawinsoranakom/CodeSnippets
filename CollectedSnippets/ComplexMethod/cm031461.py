def open_calltip(self, evalfuncs):
        """Maybe close an existing calltip and maybe open a new calltip.

        Called from (force_open|try_open|refresh)_calltip_event functions.
        """
        hp = HyperParser(self.editwin, "insert")
        sur_paren = hp.get_surrounding_brackets('(')

        # If not inside parentheses, no calltip.
        if not sur_paren:
            self.remove_calltip_window()
            return

        # If a calltip is shown for the current parentheses, do
        # nothing.
        if self.active_calltip:
            opener_line, opener_col = map(int, sur_paren[0].split('.'))
            if (
                (opener_line, opener_col) ==
                (self.active_calltip.parenline, self.active_calltip.parencol)
            ):
                return

        hp.set_index(sur_paren[0])
        try:
            expression = hp.get_expression()
        except ValueError:
            expression = None
        if not expression:
            # No expression before the opening parenthesis, e.g.
            # because it's in a string or the opener for a tuple:
            # Do nothing.
            return

        # At this point, the current index is after an opening
        # parenthesis, in a section of code, preceded by a valid
        # expression. If there is a calltip shown, it's not for the
        # same index and should be closed.
        self.remove_calltip_window()

        # Simple, fast heuristic: If the preceding expression includes
        # an opening parenthesis, it likely includes a function call.
        if not evalfuncs and (expression.find('(') != -1):
            return

        argspec = self.fetch_tip(expression)
        if not argspec:
            return
        self.active_calltip = self._calltip_window()
        self.active_calltip.showtip(argspec, sur_paren[0], sur_paren[1])