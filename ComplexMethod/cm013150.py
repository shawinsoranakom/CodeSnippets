def _has_sufficient_memory(device, size):
    device_ = torch.device(device)
    device_type = device_.type
    if device_type in ["cuda", "xpu"]:
        acc = torch.accelerator.current_accelerator()
        # Case 1: no accelerator found
        if not acc:
            return False
        # Case 2: accelerator found but not matching device type
        if acc.type != device_type:
            return True
        # Case 3: accelerator found and matching device type but not available
        if not torch.accelerator.is_available():
            return False
        # Case 4: accelerator found and matching device type and available
        gc.collect()
        torch.accelerator.empty_cache()

        if device_.index is None:
            device_ = torch.device(device_type, 0)

        if device_type == "cuda":
            return (
                torch.cuda.memory.mem_get_info(device_)[0]
                * torch.cuda.memory.get_per_process_memory_fraction(device_)
            ) >= size

        if device_type == "xpu":
            return torch.xpu.memory.mem_get_info(device_)[0] >= size

    if device_type == "xla":
        raise unittest.SkipTest("TODO: Memory availability checks for XLA?")

    if device_type != "cpu":
        raise unittest.SkipTest("Unknown device type")

    # CPU
    if not HAS_PSUTIL:
        raise unittest.SkipTest("Need psutil to determine if memory is sufficient")

    # The sanitizers have significant memory overheads
    if TEST_WITH_ASAN or TEST_WITH_TSAN or TEST_WITH_UBSAN:
        effective_size = size * 10
    else:
        effective_size = size

    # don't try using all RAM on s390x, leave some for service processes
    if IS_S390X:
        effective_size = effective_size * 2

    if psutil.virtual_memory().available < effective_size:
        gc.collect()
    return psutil.virtual_memory().available >= effective_size