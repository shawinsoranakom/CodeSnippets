def get_device_type_test_bases():
    # set type to List[Any] due to mypy list-of-union issue:
    # https://github.com/python/mypy/issues/3351
    test_bases: list[Any] = []

    if IS_SANDCASTLE or IS_FBCODE:
        if IS_REMOTE_GPU:
            # Skip if sanitizer is enabled or we're on MTIA machines
            if (
                not TEST_WITH_ASAN
                and not TEST_WITH_TSAN
                and not TEST_WITH_UBSAN
                and not TEST_WITH_MTIA
            ):
                test_bases.append(CUDATestBase)
        else:
            test_bases.append(CPUTestBase)
    else:
        test_bases.append(CPUTestBase)
        if torch.cuda.is_available():
            test_bases.append(CUDATestBase)

        if _is_privateuse1_backend_available():
            test_bases.append(PrivateUse1TestBase)
        # Disable MPS testing in generic device testing temporarily while we're
        # ramping up support.
        # elif torch.backends.mps.is_available():
        #   test_bases.append(MPSTestBase)

    return test_bases