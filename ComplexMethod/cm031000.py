def get_rerun_match_tests(self) -> FilterTuple | None:
        match_tests = []

        errors = self.errors or []
        failures = self.failures or []
        for error_list, is_error in (
            (errors, True),
            (failures, False),
        ):
            for full_name, *_ in error_list:
                match_name = normalize_test_name(full_name, is_error=is_error)
                if match_name is None:
                    # 'setUpModule (test.test_sys)': don't filter tests
                    return None
                if not match_name:
                    error_type = "ERROR" if is_error else "FAIL"
                    print_warning(f"rerun failed to parse {error_type} test name: "
                                  f"{full_name!r}: don't filter tests")
                    return None
                match_tests.append(match_name)

        if not match_tests:
            return None
        return tuple(match_tests)