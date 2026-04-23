def get_stack_trace(self, source=None, script=None,
                        breakpoint=BREAKPOINT_FN,
                        cmds_after_breakpoint=None,
                        import_site=False,
                        ignore_stderr=False):
        '''
        Run 'python -c SOURCE' under gdb with a breakpoint.

        Support injecting commands after the breakpoint is reached

        Returns the stdout from gdb

        cmds_after_breakpoint: if provided, a list of strings: gdb commands
        '''
        # We use "set breakpoint pending yes" to avoid blocking with a:
        #   Function "foo" not defined.
        #   Make breakpoint pending on future shared library load? (y or [n])
        # error, which typically happens python is dynamically linked (the
        # breakpoints of interest are to be found in the shared library)
        # When this happens, we still get:
        #   Function "textiowrapper_write" not defined.
        # emitted to stderr each time, alas.

        # Initially I had "--eval-command=continue" here, but removed it to
        # avoid repeated print breakpoints when traversing hierarchical data
        # structures

        # Generate a list of commands in gdb's language:
        commands = [
            'set breakpoint pending yes',
            'break %s' % breakpoint,

            # The tests assume that the first frame of printed
            #  backtrace will not contain program counter,
            #  that is however not guaranteed by gdb
            #  therefore we need to use 'set print address off' to
            #  make sure the counter is not there. For example:
            # #0 in PyObject_Print ...
            #  is assumed, but sometimes this can be e.g.
            # #0 0x00003fffb7dd1798 in PyObject_Print ...
            'set print address off',

            'run',
        ]

        # GDB as of 7.4 onwards can distinguish between the
        # value of a variable at entry vs current value:
        #   http://sourceware.org/gdb/onlinedocs/gdb/Variables.html
        # which leads to the selftests failing with errors like this:
        #   AssertionError: 'v@entry=()' != '()'
        # Disable this:
        if GDB_VERSION >= (7, 4):
            commands += ['set print entry-values no']

        if cmds_after_breakpoint:
            if CET_PROTECTION:
                # bpo-32962: When Python is compiled with -mcet
                # -fcf-protection, function arguments are unusable before
                # running the first instruction of the function entry point.
                # The 'next' command makes the required first step.
                commands += ['next']
            commands += cmds_after_breakpoint
        else:
            commands += ['backtrace']

        # print commands

        # Use "commands" to generate the arguments with which to invoke "gdb":
        args = ['--eval-command=%s' % cmd for cmd in commands]
        args += ["--args",
                 sys.executable]
        args.extend(subprocess._args_from_interpreter_flags())

        if not import_site:
            # -S suppresses the default 'import site'
            args += ["-S"]

        if source:
            args += ["-c", source]
        elif script:
            args += [script]

        # Use "args" to invoke gdb, capturing stdout, stderr:
        out, err = run_gdb(*args, PYTHONHASHSEED=PYTHONHASHSEED)

        if not ignore_stderr:
            for line in err.splitlines():
                print(line, file=sys.stderr)

        # bpo-34007: Sometimes some versions of the shared libraries that
        # are part of the traceback are compiled in optimised mode and the
        # Program Counter (PC) is not present, not allowing gdb to walk the
        # frames back. When this happens, the Python bindings of gdb raise
        # an exception, making the test impossible to succeed.
        if "PC not saved" in err:
            raise unittest.SkipTest("gdb cannot walk the frame object"
                                    " because the Program Counter is"
                                    " not present")

        # bpo-40019: Skip the test if gdb failed to read debug information
        # because the Python binary is optimized.
        for pattern in (
            '(frame information optimized out)',
            'Unable to read information on python frame',

            # gh-91960: On Python built with "clang -Og", gdb gets
            # "frame=<optimized out>" for _PyEval_EvalFrameDefault() parameter
            '(unable to read python frame information)',

            # gh-104736: On Python built with "clang -Og" on ppc64le,
            # "py-bt" displays a truncated or not traceback, but "where"
            # logs this error message:
            'Backtrace stopped: frame did not save the PC',

            # gh-104736: When "bt" command displays something like:
            # "#1  0x0000000000000000 in ?? ()", the traceback is likely
            # truncated or wrong.
            ' ?? ()',
        ):
            if pattern in out:
                raise unittest.SkipTest(f"{pattern!r} found in gdb output")

        return out