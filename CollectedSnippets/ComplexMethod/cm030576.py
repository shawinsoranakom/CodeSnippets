def _frame_pointers_expected(machine):
    cflags = " ".join(
        value for value in (
            sysconfig.get_config_var("PY_CORE_CFLAGS"),
            sysconfig.get_config_var("CFLAGS"),
        )
        if value
    )

    if "no-omit-frame-pointer" in cflags:
        # For example, configure adds -fno-omit-frame-pointer if Python
        # has perf trampoline (PY_HAVE_PERF_TRAMPOLINE) and Python is built
        # in debug mode.
        return True
    if "omit-frame-pointer" in cflags:
        return False

    if sys.platform == "darwin":
        # macOS x86_64/ARM64 always have frame pointer by default.
        return True

    if sys.platform == "linux":
        if machine in {"aarch64", "arm64"}:
            # 32-bit Linux is not supported
            if sys.maxsize < 2**32:
                return None
            return True
        if machine == "x86_64":
            final_opt = ""
            for opt in cflags.split():
                if opt.startswith('-O'):
                    final_opt = opt
            if final_opt in ("-O0", "-Og", "-O1"):
                # Unwinding works if the optimization level is low
                return True

            Py_ENABLE_SHARED = int(sysconfig.get_config_var('Py_ENABLE_SHARED') or '0')
            if Py_ENABLE_SHARED:
                # Unwinding does crash using gcc -O2 or gcc -O3
                # when Python is built with --enable-shared
                return "crash"
            return False

    if sys.platform == "win32":
        # MSVC ignores /Oy and /Oy- on x64/ARM64.
        if machine == "arm64":
            # Windows ARM64 guidelines recommend frame pointers (x29) for stack walking.
            return True
        elif machine == "x86_64":
            # Windows x64 uses unwind metadata; frame pointers are not required.
            return None
    return None