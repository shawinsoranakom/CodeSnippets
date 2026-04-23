def hash_storage(storage: torch.UntypedStorage, *, stable_hash: bool = False) -> str:
    import torch._dynamo
    from torch._dynamo.utils import is_compile_supported

    device_type = storage.device.type
    if stable_hash or not is_compile_supported(device_type):
        cpu_storage = storage.cpu()
        # TODO: make storage support buffer protocol so this isn't
        # necessary
        buf = (ctypes.c_byte * cpu_storage.nbytes()).from_address(
            cpu_storage.data_ptr()
        )
        sha1 = hashlib.sha1(usedforsecurity=False)
        sha1.update(buf)
        return sha1.hexdigest()

    # TODO: factor this into a random utility
    if device_type == "cpu":
        generator = torch._C.default_generator
    elif device_type == "cuda":
        generator = torch.cuda.default_generators[storage.device.index]
    elif device_type == "mps":
        generator = torch.mps._get_default_mps_generator()
    elif device_type == "xpu":
        generator = torch.xpu.default_generators[storage.device.index]
    else:
        raise AssertionError(f"unhandled device type {device_type}")
    state = generator.get_state()
    try:
        generator.manual_seed(0)
        x = torch.empty(0, dtype=torch.uint8, device=storage.device).set_(storage)  # type: ignore[call-overload]
        # The dtype-casting view cannot be compiled, and so the
        # padding/reshaping also needs to be done externally even
        # though it could be profitably fused
        pad = -x.numel() % 4
        if pad > 0:
            x = F.pad(x, (0, pad), "constant", 0)
        x = x.view(torch.int32)
        # We run the 32-bit hash five times with differing parameters to
        # reduce chance of collision
        ITER = 5
        cs = [hash_storage_kernel(x).item() for _ in range(ITER)]
        return struct.pack(">" + "i" * ITER, *cs).hex()
    finally:
        generator.set_state(state)