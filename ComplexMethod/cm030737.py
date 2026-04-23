def test_testfile(self):
        # Some tests need to be skipped on ancient OS X versions.
        # See issue #27953.
        SKIP_ON_TIGER = {'tan0064'}

        osx_version = None
        if sys.platform == 'darwin':
            version_txt = platform.mac_ver()[0]
            try:
                osx_version = tuple(map(int, version_txt.split('.')))
            except ValueError:
                pass

        fail_fmt = "{}: {}({!r}): {}"

        failures = []
        for id, fn, ar, ai, er, ei, flags in parse_testfile(test_file):
            # Skip if either the input or result is complex
            if ai != 0.0 or ei != 0.0:
                continue
            if fn in ['rect', 'polar']:
                # no real versions of rect, polar
                continue
            # Skip certain tests on OS X 10.4.
            if osx_version is not None and osx_version < (10, 5):
                if id in SKIP_ON_TIGER:
                    continue

            func = getattr(math, fn)

            if 'invalid' in flags or 'divide-by-zero' in flags:
                er = 'ValueError'
            elif 'overflow' in flags:
                er = 'OverflowError'

            try:
                result = func(ar)
            except ValueError:
                result = 'ValueError'
            except OverflowError:
                result = 'OverflowError'

            # C99+ says for math.h's sqrt: If the argument is +∞ or ±0, it is
            # returned, unmodified.  On another hand, for csqrt: If z is ±0+0i,
            # the result is +0+0i.  Lets correct zero sign of er to follow
            # first convention.
            if id in ['sqrt0002', 'sqrt0003', 'sqrt1001', 'sqrt1023']:
                er = math.copysign(er, ar)

            # Default tolerances
            ulp_tol, abs_tol = 5, 0.0

            failure = result_check(er, result, ulp_tol, abs_tol)
            if failure is None:
                continue

            msg = fail_fmt.format(id, fn, ar, failure)
            failures.append(msg)

        if failures:
            self.fail('Failures in test_testfile:\n  ' +
                      '\n  '.join(failures))