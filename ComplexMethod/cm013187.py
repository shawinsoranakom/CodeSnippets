def wrapper(*args, **kwargs):
        if not (TEST_CUDA or TEST_HPU or TEST_XPU):
            sys.exit(TEST_SKIPS["no_cuda"].exit_code)
        world_size = int(os.environ["WORLD_SIZE"])
        if TEST_CUDA and torch.cuda.device_count() < world_size:
            sys.exit(TEST_SKIPS[f"multi-gpu-{world_size}"].exit_code)
        if TEST_HPU and torch.hpu.device_count() < world_size:
            sys.exit(TEST_SKIPS[f"multi-gpu-{world_size}"].exit_code)
        if TEST_XPU and torch.xpu.device_count() < world_size:
            sys.exit(TEST_SKIPS[f"multi-gpu-{world_size}"].exit_code)

        return func(*args, **kwargs)