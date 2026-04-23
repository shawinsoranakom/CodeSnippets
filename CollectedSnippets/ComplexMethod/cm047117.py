def get_module_test_cases(module):
    """Return a suite of all test cases contained in the given module"""
    for obj in module.__dict__.values():
        if not isinstance(obj, type):
            continue
        if not issubclass(obj, case.TestCase):
            continue
        if obj.__module__ != module.__name__:
            continue

        test_case_class = obj
        test_cases = test_case_class.__dict__.items()
        if getattr(test_case_class, 'allow_inherited_tests_method', False):
            # keep iherited method for specific classes.
            # This is likely to be removed once a better solution is found
            test_cases = inspect.getmembers(test_case_class, callable)
        else:
            # sort test case to keep the initial behaviour.
            # This is likely to be removed in the future
            test_cases = sorted(test_cases, key=lambda pair: pair[0])

        for method_name, method in test_cases:
            if not callable(method):
                continue
            if not method_name.startswith('test'):
                continue
            yield test_case_class(method_name)