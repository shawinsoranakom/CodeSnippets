def skipOps(op_db, test_case_name, base_test_name, to_skip):
    all_opinfos = op_db
    for xfail in to_skip:
        op_name, variant_name, device_type, dtypes, expected_failure = xfail
        matching_opinfos = [
            o
            for o in all_opinfos
            if o.name == op_name and o.variant_test_name == variant_name
        ]
        if not (len(matching_opinfos) >= 1):
            raise AssertionError(f"Couldn't find OpInfo for {xfail}")
        for opinfo in matching_opinfos:
            decorators = list(opinfo.decorators)
            if expected_failure:
                decorator = DecorateInfo(
                    unittest.expectedFailure,
                    test_case_name,
                    base_test_name,
                    device_type=device_type,
                    dtypes=dtypes,
                )
                decorators.append(decorator)
            else:
                decorator = DecorateInfo(
                    unittest.skip("Skipped!"),
                    test_case_name,
                    base_test_name,
                    device_type=device_type,
                    dtypes=dtypes,
                )
                decorators.append(decorator)
            opinfo.decorators = tuple(decorators)

    # This decorator doesn't modify fn in any way
    def wrapped(fn):
        return fn

    return wrapped