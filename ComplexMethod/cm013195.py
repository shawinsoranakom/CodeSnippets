def wrapper(*args, **kwargs):
            if torch.cuda.is_available() and torch.cuda.device_count() >= x:
                return func(*args, **kwargs)
            if TEST_HPU and torch.hpu.device_count() >= x:
                return func(*args, **kwargs)
            if TEST_XPU and torch.xpu.device_count() >= x:
                return func(*args, **kwargs)
            if allow_cpu and not (torch.cuda.is_available() or TEST_HPU or TEST_XPU):
                return func(*args, **kwargs)
            test_skip = TEST_SKIPS[f"multi-gpu-{x}"]
            if not _maybe_handle_skip_if_lt_x_gpu(args, test_skip.message):
                sys.exit(test_skip.exit_code)