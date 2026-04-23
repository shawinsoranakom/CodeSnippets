def load_tests(loader, tests, pattern):
    if TODO_TESTS is not None:
        # Run only Arithmetic tests
        tests = loader.suiteClass()
    # Dynamically build custom test definition for each file in the test
    # directory and add the definitions to the DecimalTest class.  This
    # procedure insures that new files do not get skipped.
    for filename in os.listdir(directory):
        if '.decTest' not in filename or filename.startswith("."):
            continue
        head, tail = filename.split('.')
        if TODO_TESTS is not None and head not in TODO_TESTS:
            continue
        tester = lambda self, f=filename: self.eval_file(directory + f)
        setattr(IBMTestCases, 'test_' + head, tester)
        del filename, head, tail, tester
    for prefix, mod in ('C', C), ('Py', P):
        if not mod:
            continue
        test_class = type(prefix + 'IBMTestCases',
                          (IBMTestCases, unittest.TestCase),
                          {'decimal': mod})
        tests.addTest(loader.loadTestsFromTestCase(test_class))

    if TODO_TESTS is None:
        from doctest import DocTestSuite, IGNORE_EXCEPTION_DETAIL
        orig_context = orig_sys_decimal.getcontext().copy()
        for mod in C, P:
            if not mod:
                continue
            def setUp(slf, mod=mod):
                sys.modules['decimal'] = mod
                init(mod)
            def tearDown(slf, mod=mod):
                sys.modules['decimal'] = orig_sys_decimal
                mod.setcontext(ORIGINAL_CONTEXT[mod].copy())
                orig_sys_decimal.setcontext(orig_context.copy())
            optionflags = IGNORE_EXCEPTION_DETAIL if mod is C else 0
            sys.modules['decimal'] = mod
            tests.addTest(DocTestSuite(mod, setUp=setUp, tearDown=tearDown,
                                   optionflags=optionflags))
            sys.modules['decimal'] = orig_sys_decimal
    return tests