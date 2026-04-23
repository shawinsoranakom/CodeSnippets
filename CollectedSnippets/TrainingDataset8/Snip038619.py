def _test_dependent_option():
            """Depend on the value of _test.independentOption."""
            return config.get_option("_test.independentOption")