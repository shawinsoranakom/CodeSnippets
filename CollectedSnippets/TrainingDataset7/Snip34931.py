def get_test_methods_names(suite):
        return [t.__class__.__name__ + "." + t._testMethodName for t in suite._tests]