def test_re_tests(self):
        're_tests test suite'
        from test.re_tests import tests, FAIL, SYNTAX_ERROR
        for t in tests:
            pattern = s = outcome = repl = expected = None
            if len(t) == 5:
                pattern, s, outcome, repl, expected = t
            elif len(t) == 3:
                pattern, s, outcome = t
            else:
                raise ValueError('Test tuples should have 3 or 5 fields', t)

            with self.subTest(pattern=pattern, string=s):
                if outcome == SYNTAX_ERROR:  # Expected a syntax error
                    with self.assertRaises(re.PatternError):
                        re.compile(pattern)
                    continue

                obj = re.compile(pattern)
                result = obj.search(s)
                if outcome == FAIL:
                    self.assertIsNone(result, 'Succeeded incorrectly')
                    continue

                with self.subTest():
                    self.assertTrue(result, 'Failed incorrectly')
                    # Matched, as expected, so now we compute the
                    # result string and compare it to our expected result.
                    start, end = result.span(0)
                    vardict = {'found': result.group(0),
                               'groups': result.group(),
                               'flags': result.re.flags}
                    for i in range(1, 100):
                        try:
                            gi = result.group(i)
                            # Special hack because else the string concat fails:
                            if gi is None:
                                gi = "None"
                        except IndexError:
                            gi = "Error"
                        vardict['g%d' % i] = gi
                    for i in result.re.groupindex.keys():
                        try:
                            gi = result.group(i)
                            if gi is None:
                                gi = "None"
                        except IndexError:
                            gi = "Error"
                        vardict[i] = gi
                    self.assertEqual(eval(repl, vardict), expected,
                                     'grouping error')

                # Try the match with both pattern and string converted to
                # bytes, and check that it still succeeds.
                try:
                    bpat = bytes(pattern, "ascii")
                    bs = bytes(s, "ascii")
                except UnicodeEncodeError:
                    # skip non-ascii tests
                    pass
                else:
                    with self.subTest('bytes pattern match'):
                        obj = re.compile(bpat)
                        self.assertTrue(obj.search(bs))

                    # Try the match with LOCALE enabled, and check that it
                    # still succeeds.
                    with self.subTest('locale-sensitive match'):
                        obj = re.compile(bpat, re.LOCALE)
                        result = obj.search(bs)
                        if result is None:
                            print('=== Fails on locale-sensitive match', t)

                # Try the match with the search area limited to the extent
                # of the match and see if it still succeeds.  \B will
                # break (because it won't match at the end or start of a
                # string), so we'll ignore patterns that feature it.
                if (pattern[:2] != r'\B' and pattern[-2:] != r'\B'
                            and result is not None):
                    with self.subTest('range-limited match'):
                        obj = re.compile(pattern)
                        self.assertTrue(obj.search(s, start, end + 1))

                # Try the match with IGNORECASE enabled, and check that it
                # still succeeds.
                with self.subTest('case-insensitive match'):
                    obj = re.compile(pattern, re.IGNORECASE)
                    self.assertTrue(obj.search(s))

                # Try the match with UNICODE locale enabled, and check
                # that it still succeeds.
                with self.subTest('unicode-sensitive match'):
                    obj = re.compile(pattern, re.UNICODE)
                    self.assertTrue(obj.search(s))