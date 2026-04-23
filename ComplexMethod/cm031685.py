def get_target(host: str) -> _COFF32 | _COFF64 | _ELF | _MachO:
    """Build a _Target for the given host "triple" and options."""
    optimizer: type[_optimizers.Optimizer]
    target: _COFF32 | _COFF64 | _ELF | _MachO
    if re.fullmatch(r"aarch64-apple-darwin.*", host):
        host = "aarch64-apple-darwin"
        condition = "defined(__aarch64__) && defined(__APPLE__)"
        optimizer = _optimizers.OptimizerAArch64
        target = _MachO(host, condition, optimizer=optimizer)
    elif re.fullmatch(r"aarch64-pc-windows-msvc", host):
        host = "aarch64-pc-windows-msvc"
        condition = "defined(_M_ARM64)"
        args = ["-fms-runtime-lib=dll"]
        optimizer = _optimizers.OptimizerAArch64
        target = _COFF64(host, condition, args=args, optimizer=optimizer)
    elif re.fullmatch(r"aarch64-.*-linux-gnu", host):
        host = "aarch64-unknown-linux-gnu"
        condition = "defined(__aarch64__) && defined(__linux__)"
        # -mno-outline-atomics: Keep intrinsics from being emitted.
        args = ["-fpic", "-mno-outline-atomics"]
        optimizer = _optimizers.OptimizerAArch64
        target = _ELF(
            host, condition, args=args, optimizer=optimizer, frame_pointers=True
        )
    elif re.fullmatch(r"i686-pc-windows-msvc", host):
        host = "i686-pc-windows-msvc"
        condition = "defined(_M_IX86)"
        # -Wno-ignored-attributes: __attribute__((preserve_none)) is not supported here.
        # -mno-sse: Use x87 FPU instead of SSE for float math. The COFF32
        # stencil converter cannot handle _xmm register references.
        args = ["-DPy_NO_ENABLE_SHARED", "-Wno-ignored-attributes", "-mno-sse"]
        optimizer = _optimizers.OptimizerX86
        target = _COFF32(host, condition, args=args, optimizer=optimizer)
    elif re.fullmatch(r"x86_64-apple-darwin.*", host):
        host = "x86_64-apple-darwin"
        condition = "defined(__x86_64__) && defined(__APPLE__)"
        optimizer = _optimizers.OptimizerX86
        target = _MachO(host, condition, optimizer=optimizer)
    elif re.fullmatch(r"x86_64-pc-windows-msvc", host):
        host = "x86_64-pc-windows-msvc"
        condition = "defined(_M_X64)"
        args = ["-fms-runtime-lib=dll"]
        optimizer = _optimizers.OptimizerX86
        target = _COFF64(host, condition, args=args, optimizer=optimizer)
    elif re.fullmatch(r"x86_64-.*-linux-gnu", host):
        host = "x86_64-unknown-linux-gnu"
        condition = "defined(__x86_64__) && defined(__linux__)"
        args = ["-fno-pic", "-mcmodel=medium", "-mlarge-data-threshold=0", "-fno-plt"]
        optimizer = _optimizers.OptimizerX86
        target = _ELF(
            host, condition, args=args, optimizer=optimizer, frame_pointers=True
        )
    else:
        raise ValueError(host)
    return target