def do_ignore(self, arg):
        """ignore bpnumber [count]

        Set the ignore count for the given breakpoint number.  If
        count is omitted, the ignore count is set to 0.  A breakpoint
        becomes active when the ignore count is zero.  When non-zero,
        the count is decremented each time the breakpoint is reached
        and the breakpoint is not disabled and any associated
        condition evaluates to true.
        """
        if not arg:
            self._print_invalid_arg(arg)
            return
        args = arg.split()
        if not args:
            self.error('Breakpoint number expected')
            return
        if len(args) == 1:
            count = 0
        elif len(args) == 2:
            try:
                count = int(args[1])
            except ValueError:
                self._print_invalid_arg(arg)
                return
        else:
            self._print_invalid_arg(arg)
            return
        try:
            bp = self.get_bpbynumber(args[0].strip())
        except ValueError as err:
            self.error(err)
        else:
            bp.ignore = count
            if count > 0:
                if count > 1:
                    countstr = '%d crossings' % count
                else:
                    countstr = '1 crossing'
                self.message('Will ignore next %s of breakpoint %d.' %
                             (countstr, bp.number))
            else:
                self.message('Will stop next time breakpoint %d is reached.'
                             % bp.number)