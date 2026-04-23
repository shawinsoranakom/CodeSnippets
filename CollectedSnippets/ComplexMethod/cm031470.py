def run_module_event(self, event, *, customize=False):
        """Run the module after setting up the environment.

        First check the syntax.  Next get customization.  If OK, make
        sure the shell is active and then transfer the arguments, set
        the run environment's working directory to the directory of the
        module being executed and also add that directory to its
        sys.path if not already included.
        """
        if macosx.isCocoaTk() and (time.perf_counter() - self.perf < .05):
            return 'break'
        if isinstance(self.editwin, outwin.OutputWindow):
            self.editwin.text.bell()
            return 'break'
        filename = self.getfilename()
        if not filename:
            return 'break'
        code = self.checksyntax(filename)
        if not code:
            return 'break'
        if not self.tabnanny(filename):
            return 'break'
        if customize:
            title = f"Customize {self.editwin.short_title()} Run"
            run_args = CustomRun(self.shell.text, title,
                                 cli_args=self.cli_args).result
            if not run_args:  # User cancelled.
                return 'break'
        self.cli_args, restart = run_args if customize else ([], True)
        interp = self.shell.interp
        if pyshell.use_subprocess and restart:
            interp.restart_subprocess(
                    with_cwd=False, filename=filename)
        dirname = os.path.dirname(filename)
        argv = [filename]
        if self.cli_args:
            argv += self.cli_args
        interp.runcommand(f"""if 1:
            __file__ = {filename!r}
            import sys as _sys
            from os.path import basename as _basename
            argv = {argv!r}
            if (not _sys.argv or
                _basename(_sys.argv[0]) != _basename(__file__) or
                len(argv) > 1):
                _sys.argv = argv
            import os as _os
            _os.chdir({dirname!r})
            del _sys, argv, _basename, _os
            \n""")
        interp.prepend_syspath(filename)
        # XXX KBK 03Jul04 When run w/o subprocess, runtime warnings still
        #         go to __stderr__.  With subprocess, they go to the shell.
        #         Need to change streams in pyshell.ModifiedInterpreter.
        interp.runcode(code)
        return 'break'