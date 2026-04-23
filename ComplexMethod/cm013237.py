def wrapper(*args, **kwargs):
        if has_triton():
            return test_func(*args, **kwargs)

        spec = _device_spec_from_test_call(args, kwargs)
        if spec is None and args:
            spec = getattr(args[0], "device_type", None)
        if spec is not None and _is_cpu_device_type(spec):
            try:
                return test_func(*args, **kwargs)
            except ImportError as e:
                # This except block required only for TestUtilsCPU::test_get_device_tflops_cpu
                # test_get_device_tflops imports triton directly in its body — even for CPU
                if "triton" in str(e).lower():
                    import pytest
                    pytest.xfail(f"Triton not available (device={spec!r}): {e}")
                raise

        import pytest
        device_info = f" (device={spec!r})" if spec is not None else ""
        pytest.xfail(f"Triton not available{device_info}")