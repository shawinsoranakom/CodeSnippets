def run(self, test, compileflags=None, out=None, clear_globs=True):
        """
        Run the examples in `test`, and display the results using the
        writer function `out`.

        The examples are run in the namespace `test.globs`.  If
        `clear_globs` is true (the default), then this namespace will
        be cleared after the test runs, to help with garbage
        collection.  If you would like to examine the namespace after
        the test completes, then use `clear_globs=False`.

        `compileflags` gives the set of flags that should be used by
        the Python compiler when running the examples.  If not
        specified, then it will default to the set of future-import
        flags that apply to `globs`.

        The output of each example is checked using
        `DocTestRunner.check_output`, and the results are formatted by
        the `DocTestRunner.report_*` methods.
        """
        self.test = test

        if compileflags is None:
            compileflags = _extract_future_flags(test.globs)

        save_stdout = sys.stdout
        if out is None:
            encoding = save_stdout.encoding
            if encoding is None or encoding.lower() == 'utf-8':
                out = save_stdout.write
            else:
                # Use backslashreplace error handling on write
                def out(s):
                    s = str(s.encode(encoding, 'backslashreplace'), encoding)
                    save_stdout.write(s)
        sys.stdout = self._fakeout

        # Patch pdb.set_trace to restore sys.stdout during interactive
        # debugging (so it's not still redirected to self._fakeout).
        # Note that the interactive output will go to *our*
        # save_stdout, even if that's not the real sys.stdout; this
        # allows us to write test cases for the set_trace behavior.
        save_trace = sys.gettrace()
        save_set_trace = pdb.set_trace
        self.debugger = _OutputRedirectingPdb(save_stdout)
        self.debugger.reset()
        pdb.set_trace = self.debugger.set_trace

        # Patch linecache.getlines, so we can see the example's source
        # when we're inside the debugger.
        self.save_linecache_getlines = linecache.getlines
        linecache.getlines = self.__patched_linecache_getlines

        # Make sure sys.displayhook just prints the value to stdout
        save_displayhook = sys.displayhook
        sys.displayhook = sys.__displayhook__
        saved_can_colorize = _colorize.can_colorize
        _colorize.can_colorize = lambda *args, **kwargs: False
        color_variables = {"PYTHON_COLORS": None, "FORCE_COLOR": None}
        for key in color_variables:
            color_variables[key] = os.environ.pop(key, None)
        try:
            return self.__run(test, compileflags, out)
        finally:
            sys.stdout = save_stdout
            pdb.set_trace = save_set_trace
            sys.settrace(save_trace)
            linecache.getlines = self.save_linecache_getlines
            sys.displayhook = save_displayhook
            _colorize.can_colorize = saved_can_colorize
            for key, value in color_variables.items():
                if value is not None:
                    os.environ[key] = value
            if clear_globs:
                test.globs.clear()
                import builtins
                builtins._ = None