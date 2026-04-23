def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(doctests))
    return tests