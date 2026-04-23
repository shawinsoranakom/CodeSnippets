def get_selected_tests(options) -> list[str]:
    selected_tests = options.include

    # filter if there's JIT only and distributed only test options
    if options.jit:
        selected_tests = list(
            filter(lambda test_name: "jit" in test_name, selected_tests)
        )

    if options.distributed_tests:
        selected_tests = list(
            filter(lambda test_name: test_name in DISTRIBUTED_TESTS, selected_tests)
        )

    # Filter to only run core tests when --core option is specified
    if options.core:
        selected_tests = list(
            filter(lambda test_name: test_name in CORE_TEST_LIST, selected_tests)
        )

    if options.include_cpython_tests:
        selected_tests = list(
            filter(lambda test_name: test_name in CPYTHON_TESTS, selected_tests)
        )

    # Filter to only run dynamo tests when --include-dynamo-core-tests option is specified
    if options.include_dynamo_core_tests:
        selected_tests = list(
            filter(lambda test_name: test_name in DYNAMO_CORE_TESTS, selected_tests)
        )

    # Filter to only run dynamo tests when --include-inductor-core-tests option is specified
    if options.include_inductor_core_tests:
        selected_tests = list(
            filter(lambda test_name: test_name in INDUCTOR_TESTS, selected_tests)
        )

    # Filter to only run functorch tests when --functorch option is specified
    if options.functorch:
        selected_tests = list(
            filter(lambda test_name: test_name in FUNCTORCH_TESTS, selected_tests)
        )

    # Filter to only run einops tests when --einops option is specified
    if options.einops:
        selected_tests = list(
            filter(
                lambda test_name: test_name.startswith("dynamo/test_einops"),
                selected_tests,
            )
        )

    if options.cpp:
        selected_tests = list(
            filter(lambda test_name: test_name in CPP_TESTS, selected_tests)
        )
    else:
        # Exclude all C++ tests otherwise as they are still handled differently
        # than Python test at the moment
        options.exclude.extend(CPP_TESTS)

    if options.mps:
        os.environ["PYTORCH_TESTING_DEVICE_ONLY_FOR"] = "mps"
        selected_tests = [
            "test_ops",
            "test_mps",
            "test_metal",
            "test_modules",
            "nn/test_convolution",
            "nn/test_dropout",
            "nn/test_pooling",
            "test_view_ops",
            "test_nn",
            "inductor/test_mps_basic",
            "inductor/test_torchinductor",
            "inductor/test_aot_inductor",
            "inductor/test_torchinductor_dynamic_shapes",
        ]
    else:
        # Exclude mps-only tests otherwise
        options.exclude.extend(["test_mps", "test_metal"])

    if options.xpu:
        selected_tests = exclude_tests(XPU_BLOCKLIST, selected_tests, "on XPU")
    else:
        # Exclude all xpu specific tests otherwise
        options.exclude.extend(XPU_TEST)

    if options.openreg:
        selected_tests = ["test_openreg"]
    else:
        options.exclude.append("test_openreg")

    # Filter to only run onnx tests when --onnx option is specified
    onnx_tests = [tname for tname in selected_tests if tname in ONNX_TESTS]
    if options.onnx:
        selected_tests = onnx_tests
    else:
        # Exclude all onnx tests otherwise
        options.exclude.extend(onnx_tests)

    # process exclusion
    if options.exclude_jit_executor:
        options.exclude.extend(JIT_EXECUTOR_TESTS)

    if options.exclude_distributed_tests:
        options.exclude.extend(DISTRIBUTED_TESTS)

    if options.exclude_inductor_tests:
        options.exclude.extend(INDUCTOR_TESTS)

    if options.exclude_torch_export_tests:
        options.exclude.extend(TORCH_EXPORT_TESTS)

    if options.exclude_aot_dispatch_tests:
        options.exclude.extend(AOT_DISPATCH_TESTS)

    if options.exclude_quantization_tests:
        options.exclude.extend(QUANTIZATION_TESTS)

    # these tests failing in CUDA 11.6 temporary disabling. issue https://github.com/pytorch/pytorch/issues/75375
    if torch.version.cuda is not None:
        options.exclude.extend(["distributions/test_constraints"])

    # these tests failing in Python 3.12 temporarily disabling
    if sys.version_info >= (3, 12):
        options.exclude.extend(
            [
                "functorch/test_dims",
                "functorch/test_rearrange",
                "functorch/test_parsing",
                "functorch/test_memory_efficient_fusion",
                "torch_np/numpy_tests/core/test_multiarray",
            ]
        )

    if sys.version_info[:2] < (3, 13) or sys.version_info[:2] >= (3, 14):
        # Skip tests for older Python versions as they may use syntax or features
        # not supported in those versions
        options.exclude.extend(
            [test for test in selected_tests if test.startswith("dynamo/cpython/3_13/")]
        )

    selected_tests = exclude_tests(options.exclude, selected_tests)

    if IS_WINDOWS and not options.ignore_win_blocklist:
        from torch.testing._internal.common_cuda import SM120OrLater, SM89OrLater

        # Disable tests on Windows for SM89 and later - tests failing in ci
        # Enable tests after fixing the failures
        if SM89OrLater:
            WINDOWS_BLOCKLIST.extend(
                [
                    # Windows fatal exception / access violation
                    "functorch/test_aotdispatch",
                    "functorch/test_control_flow",
                    "nn/test_convolution",
                    "profiler/test_profiler",
                    "test_modules",
                    "test_expanded_weights",
                    "test_jit",
                    "test_nested_tensor",
                    "test_nestedtensor",
                    "test_nn",
                    # DLL load failed errors, missing dependencies
                    "test_custom_ops",
                    "test_testing",
                    # Features not supported on Windows ( e.g. rowwise scaling)
                    "test_decomp",
                    "test_transformers",
                    "test_ops",
                    # Output mismatch errors and long running tests
                    "test_linalg",
                    "test_matmul_cuda",
                    "functorch/test_ops",
                    "test_scaled_matmul_cuda",
                ]
            )

        # Disable tests on Windows for SM120 and later - tests failing in ci
        # Enable tests after fixing the failures
        if SM120OrLater:
            WINDOWS_BLOCKLIST.extend(
                [
                    # test_api fails on Windows SM120+. Triage pending.
                    "cpp/test_api",
                ]
            )

        target_arch = os.environ.get("VSCMD_ARG_TGT_ARCH")
        if target_arch != "x64":
            WINDOWS_BLOCKLIST.append("cpp_extensions_aot_no_ninja")
            WINDOWS_BLOCKLIST.append("cpp_extensions_aot_ninja")
            WINDOWS_BLOCKLIST.append("cpp_extensions_jit")
            WINDOWS_BLOCKLIST.append("jit")
            WINDOWS_BLOCKLIST.append("jit_fuser")

        selected_tests = exclude_tests(WINDOWS_BLOCKLIST, selected_tests, "on Windows")

    elif TEST_WITH_ROCM:
        selected_tests = exclude_tests(ROCM_BLOCKLIST, selected_tests, "on ROCm")

    elif IS_S390X:
        selected_tests = exclude_tests(S390X_BLOCKLIST, selected_tests, "on s390x")
        selected_tests = exclude_tests(
            DISTRIBUTED_TESTS,
            selected_tests,
            "Skip distributed tests on s390x",
        )

    # skip all distributed tests if distributed package is not available.
    if not dist.is_available():
        selected_tests = exclude_tests(
            DISTRIBUTED_TESTS,
            selected_tests,
            "PyTorch is built without distributed support.",
        )

    # skip tests that require LAPACK when it's not available
    if not torch._C.has_lapack:
        selected_tests = exclude_tests(
            TESTS_REQUIRING_LAPACK,
            selected_tests,
            "PyTorch is built without LAPACK support.",
        )

    if TEST_WITH_SLOW_GRADCHECK:
        selected_tests = exclude_tests(
            TESTS_NOT_USING_GRADCHECK,
            selected_tests,
            "Running in slow gradcheck mode, skipping tests that don't use gradcheck.",
            exact_match=True,
        )

    selected_tests = [parse_test_module(x) for x in selected_tests]
    return selected_tests