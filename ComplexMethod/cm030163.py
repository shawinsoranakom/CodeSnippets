def do_break(self, arg, temporary=False):
        """b(reak) [ ([filename:]lineno | function) [, condition] ]

        Without argument, list all breaks.

        With a line number argument, set a break at this line in the
        current file.  With a function name, set a break at the first
        executable line of that function.  If a second argument is
        present, it is a string specifying an expression which must
        evaluate to true before the breakpoint is honored.

        The line number may be prefixed with a filename and a colon,
        to specify a breakpoint in another file (probably one that
        hasn't been loaded yet).  The file is searched for on
        sys.path; the .py suffix may be omitted.
        """
        if not arg:
            if self.breaks:  # There's at least one
                self.message("Num Type         Disp Enb   Where")
                for bp in bdb.Breakpoint.bpbynumber:
                    if bp:
                        self.message(bp.bpformat())
            return
        # parse arguments; comma has lowest precedence
        # and cannot occur in filename
        filename = None
        lineno = None
        cond = None
        module_globals = None
        comma = arg.find(',')
        if comma > 0:
            # parse stuff after comma: "condition"
            cond = arg[comma+1:].lstrip()
            if err := self._compile_error_message(cond):
                self.error('Invalid condition %s: %r' % (cond, err))
                return
            arg = arg[:comma].rstrip()
        # parse stuff before comma: [filename:]lineno | function
        colon = arg.rfind(':')
        funcname = None
        if colon >= 0:
            filename = arg[:colon].rstrip()
            f = self.lookupmodule(filename)
            if not f:
                self.error('%r not found from sys.path' % filename)
                return
            else:
                filename = f
            arg = arg[colon+1:].lstrip()
            try:
                lineno = int(arg)
            except ValueError:
                self.error('Bad lineno: %s' % arg)
                return
        else:
            # no colon; can be lineno or function
            try:
                lineno = int(arg)
            except ValueError:
                try:
                    func = eval(arg,
                                self.curframe.f_globals,
                                self.curframe.f_locals)
                except:
                    func = arg
                try:
                    if hasattr(func, '__func__'):
                        func = func.__func__
                    code = func.__code__
                    #use co_name to identify the bkpt (function names
                    #could be aliased, but co_name is invariant)
                    funcname = code.co_name
                    lineno = find_first_executable_line(code)
                    filename = code.co_filename
                    module_globals = func.__globals__
                except:
                    # last thing to try
                    (ok, filename, ln) = self.lineinfo(arg)
                    if not ok:
                        self.error('The specified object %r is not a function '
                                   'or was not found along sys.path.' % arg)
                        return
                    funcname = ok # ok contains a function name
                    lineno = int(ln)
        if not filename:
            filename = self.defaultFile()
        filename = self.canonic(filename)
        # Check for reasonable breakpoint
        line = self.checkline(filename, lineno, module_globals)
        if line:
            # now set the break point
            err = self.set_break(filename, line, temporary, cond, funcname)
            if err:
                self.error(err)
            else:
                bp = self.get_breaks(filename, line)[-1]
                self.message("Breakpoint %d at %s:%d" %
                             (bp.number, bp.file, bp.line))