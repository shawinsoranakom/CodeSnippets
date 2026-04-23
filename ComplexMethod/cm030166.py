def do_condition(self, arg):
        """condition bpnumber [condition]

        Set a new condition for the breakpoint, an expression which
        must evaluate to true before the breakpoint is honored.  If
        condition is absent, any existing condition is removed; i.e.,
        the breakpoint is made unconditional.
        """
        if not arg:
            self._print_invalid_arg(arg)
            return
        args = arg.split(' ', 1)
        try:
            cond = args[1]
            if err := self._compile_error_message(cond):
                self.error('Invalid condition %s: %r' % (cond, err))
                return
        except IndexError:
            cond = None
        try:
            bp = self.get_bpbynumber(args[0].strip())
        except IndexError:
            self.error('Breakpoint number expected')
        except ValueError as err:
            self.error(err)
        else:
            bp.cond = cond
            if not cond:
                self.message('Breakpoint %d is now unconditional.' % bp.number)
            else:
                self.message('New condition set for breakpoint %d.' % bp.number)