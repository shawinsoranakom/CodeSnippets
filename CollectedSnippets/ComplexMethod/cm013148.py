def get_desired_device_type_test_bases(
    except_for=None, only_for=None, include_lazy=False, allow_mps=False, allow_xpu=False
):
    # allow callers to specifically opt tests into being tested on MPS, similar to `include_lazy`
    test_bases = device_type_test_bases.copy()
    if allow_mps and TEST_MPS and MPSTestBase not in test_bases:
        test_bases.append(MPSTestBase)
    if allow_xpu and TEST_XPU and XPUTestBase not in test_bases:
        test_bases.append(XPUTestBase)
    if TEST_HPU and HPUTestBase not in test_bases:
        test_bases.append(HPUTestBase)
    # Filter out the device types based on user inputs
    desired_device_type_test_bases = filter_desired_device_types(
        test_bases, except_for, only_for
    )
    if include_lazy:
        # Note [Lazy Tensor tests in device agnostic testing]
        # Right now, test_view_ops.py runs with LazyTensor.
        # We don't want to opt every device-agnostic test into using the lazy device,
        # because many of them will fail.
        # So instead, the only way to opt a specific device-agnostic test file into
        # lazy tensor testing is with include_lazy=True
        if IS_FBCODE:
            print(
                "TorchScript backend not yet supported in FBCODE/OVRSOURCE builds",
                file=sys.stderr,
            )
        else:
            desired_device_type_test_bases.append(LazyTestBase)

    def split_if_not_empty(x: str):
        return x.split(",") if x else []

    # run some cuda testcases on other devices if available
    # Usage:
    # export PYTORCH_TESTING_DEVICE_FOR_CUSTOM=privateuse1
    env_custom_only_for = split_if_not_empty(
        os.getenv(PYTORCH_TESTING_DEVICE_FOR_CUSTOM_KEY, "")
    )
    if env_custom_only_for:
        desired_device_type_test_bases += filter(
            lambda x: x.device_type in env_custom_only_for, test_bases
        )
        desired_device_type_test_bases = list(set(desired_device_type_test_bases))

    # Filter out the device types based on environment variables if available
    # Usage:
    # export PYTORCH_TESTING_DEVICE_ONLY_FOR=cuda,cpu
    # export PYTORCH_TESTING_DEVICE_EXCEPT_FOR=xla
    env_only_for = split_if_not_empty(
        os.getenv(PYTORCH_TESTING_DEVICE_ONLY_FOR_KEY, "")
    )
    env_except_for = split_if_not_empty(
        os.getenv(PYTORCH_TESTING_DEVICE_EXCEPT_FOR_KEY, "")
    )

    return filter_desired_device_types(
        desired_device_type_test_bases, env_except_for, env_only_for
    )