def filter_desired_device_types(device_type_test_bases, except_for=None, only_for=None):
    # device type cannot appear in both except_for and only_for
    intersect = set(except_for if except_for else []) & set(
        only_for if only_for else []
    )
    if intersect:
        raise AssertionError(
            f"device ({intersect}) appeared in both except_for and only_for"
        )

    # Replace your privateuse1 backend name with 'privateuse1'
    # This handles the case where PrivateUse1TestBase.device_type has been
    # changed from "privateuse1" to the actual backend name (e.g., "openreg")
    # by setUpClass being called during previous instantiate_device_type_tests calls
    if _is_privateuse1_backend_available():
        privateuse1_backend_name = torch._C._get_privateuse1_backend_name()

        def func_replace(x: str) -> str:
            return x.replace(privateuse1_backend_name, "privateuse1")

        except_for = (
            ([func_replace(x) for x in except_for] if except_for is not None else None)
            if not isinstance(except_for, str)
            else func_replace(except_for)
        )
        only_for = (
            ([func_replace(x) for x in only_for] if only_for is not None else None)
            if not isinstance(only_for, str)
            else func_replace(only_for)
        )
    else:

        def func_replace(x: str) -> str:
            return x

    if except_for:
        device_type_test_bases = filter(
            lambda x: func_replace(x.device_type) not in except_for,
            device_type_test_bases,
        )
    if only_for:
        device_type_test_bases = filter(
            lambda x: func_replace(x.device_type) in only_for,
            device_type_test_bases,
        )

    return list(device_type_test_bases)