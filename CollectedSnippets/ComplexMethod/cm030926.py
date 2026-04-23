def _check_recursive_traceback_display(self, render_exc):
        # Always show full diffs when this test fails
        # Note that rearranging things may require adjusting
        # the relative line numbers in the expected tracebacks
        self.maxDiff = None

        # Check hitting the recursion limit
        def f():
            f()

        with captured_output("stderr") as stderr_f:
            try:
                f()
            except RecursionError:
                render_exc()
            else:
                self.fail("no recursion occurred")

        lineno_f = f.__code__.co_firstlineno
        result_f = (
            'Traceback (most recent call last):\n'
            f'  File "{__file__}", line {lineno_f+5}, in _check_recursive_traceback_display\n'
            '    f()\n'
            '    ~^^\n'
            f'  File "{__file__}", line {lineno_f+1}, in f\n'
            '    f()\n'
            '    ~^^\n'
            f'  File "{__file__}", line {lineno_f+1}, in f\n'
            '    f()\n'
            '    ~^^\n'
            f'  File "{__file__}", line {lineno_f+1}, in f\n'
            '    f()\n'
            '    ~^^\n'
            # XXX: The following line changes depending on whether the tests
            # are run through the interactive interpreter or with -m
            # It also varies depending on the platform (stack size)
            # Fortunately, we don't care about exactness here, so we use regex
            r'  \[Previous line repeated (\d+) more times\]' '\n'
            'RecursionError: maximum recursion depth exceeded\n'
        )

        expected = self._maybe_filter_debug_ranges(result_f.splitlines())
        actual = stderr_f.getvalue().splitlines()

        # Check the output text matches expectations
        # 2nd last line contains the repetition count
        self.assertEqual(actual[:-2], expected[:-2])
        self.assertRegex(actual[-2], expected[-2])
        # last line can have additional text appended
        self.assertIn(expected[-1], actual[-1])

        # Check the recursion count is roughly as expected
        rec_limit = sys.getrecursionlimit()
        self.assertIn(int(re.search(r"\d+", actual[-2]).group()), range(rec_limit-60, rec_limit))

        # Check a known (limited) number of recursive invocations
        def g(count=10):
            if count:
                return g(count-1) + 1
            raise ValueError

        with captured_output("stderr") as stderr_g:
            try:
                g()
            except ValueError:
                render_exc()
            else:
                self.fail("no value error was raised")

        lineno_g = g.__code__.co_firstlineno
        result_g = (
            f'  File "{__file__}", line {lineno_g+2}, in g\n'
            '    return g(count-1) + 1\n'
            '           ~^^^^^^^^^\n'
            f'  File "{__file__}", line {lineno_g+2}, in g\n'
            '    return g(count-1) + 1\n'
            '           ~^^^^^^^^^\n'
            f'  File "{__file__}", line {lineno_g+2}, in g\n'
            '    return g(count-1) + 1\n'
            '           ~^^^^^^^^^\n'
            '  [Previous line repeated 7 more times]\n'
            f'  File "{__file__}", line {lineno_g+3}, in g\n'
            '    raise ValueError\n'
            'ValueError\n'
        )
        tb_line = (
            'Traceback (most recent call last):\n'
            f'  File "{__file__}", line {lineno_g+7}, in _check_recursive_traceback_display\n'
            '    g()\n'
            '    ~^^\n'
        )
        expected = self._maybe_filter_debug_ranges((tb_line + result_g).splitlines())
        actual = stderr_g.getvalue().splitlines()
        self.assertEqual(actual, expected)

        # Check 2 different repetitive sections
        def h(count=10):
            if count:
                return h(count-1)
            g()

        with captured_output("stderr") as stderr_h:
            try:
                h()
            except ValueError:
                render_exc()
            else:
                self.fail("no value error was raised")

        lineno_h = h.__code__.co_firstlineno
        result_h = (
            'Traceback (most recent call last):\n'
            f'  File "{__file__}", line {lineno_h+7}, in _check_recursive_traceback_display\n'
            '    h()\n'
            '    ~^^\n'
            f'  File "{__file__}", line {lineno_h+2}, in h\n'
            '    return h(count-1)\n'
            f'  File "{__file__}", line {lineno_h+2}, in h\n'
            '    return h(count-1)\n'
            f'  File "{__file__}", line {lineno_h+2}, in h\n'
            '    return h(count-1)\n'
            '  [Previous line repeated 7 more times]\n'
            f'  File "{__file__}", line {lineno_h+3}, in h\n'
            '    g()\n'
            '    ~^^\n'
        )
        expected = self._maybe_filter_debug_ranges((result_h + result_g).splitlines())
        actual = stderr_h.getvalue().splitlines()
        self.assertEqual(actual, expected)

        # Check the boundary conditions. First, test just below the cutoff.
        with captured_output("stderr") as stderr_g:
            try:
                g(traceback._RECURSIVE_CUTOFF)
            except ValueError:
                render_exc()
            else:
                self.fail("no error raised")
        result_g = (
            f'  File "{__file__}", line {lineno_g+2}, in g\n'
            '    return g(count-1) + 1\n'
            '           ~^^^^^^^^^\n'
            f'  File "{__file__}", line {lineno_g+2}, in g\n'
            '    return g(count-1) + 1\n'
            '           ~^^^^^^^^^\n'
            f'  File "{__file__}", line {lineno_g+2}, in g\n'
            '    return g(count-1) + 1\n'
            '           ~^^^^^^^^^\n'
            f'  File "{__file__}", line {lineno_g+3}, in g\n'
            '    raise ValueError\n'
            'ValueError\n'
        )
        tb_line = (
            'Traceback (most recent call last):\n'
            f'  File "{__file__}", line {lineno_g+77}, in _check_recursive_traceback_display\n'
            '    g(traceback._RECURSIVE_CUTOFF)\n'
            '    ~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n'
        )
        expected = self._maybe_filter_debug_ranges((tb_line + result_g).splitlines())
        actual = stderr_g.getvalue().splitlines()
        self.assertEqual(actual, expected)

        # Second, test just above the cutoff.
        with captured_output("stderr") as stderr_g:
            try:
                g(traceback._RECURSIVE_CUTOFF + 1)
            except ValueError:
                render_exc()
            else:
                self.fail("no error raised")
        result_g = (
            f'  File "{__file__}", line {lineno_g+2}, in g\n'
            '    return g(count-1) + 1\n'
            '           ~^^^^^^^^^\n'
            f'  File "{__file__}", line {lineno_g+2}, in g\n'
            '    return g(count-1) + 1\n'
            '           ~^^^^^^^^^\n'
            f'  File "{__file__}", line {lineno_g+2}, in g\n'
            '    return g(count-1) + 1\n'
            '           ~^^^^^^^^^\n'
            '  [Previous line repeated 1 more time]\n'
            f'  File "{__file__}", line {lineno_g+3}, in g\n'
            '    raise ValueError\n'
            'ValueError\n'
        )
        tb_line = (
            'Traceback (most recent call last):\n'
            f'  File "{__file__}", line {lineno_g+109}, in _check_recursive_traceback_display\n'
            '    g(traceback._RECURSIVE_CUTOFF + 1)\n'
            '    ~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n'
        )
        expected = self._maybe_filter_debug_ranges((tb_line + result_g).splitlines())
        actual = stderr_g.getvalue().splitlines()
        self.assertEqual(actual, expected)