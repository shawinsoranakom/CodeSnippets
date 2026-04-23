def _get_optimization_cflags(
    cpp_compiler: str, min_optimize: bool = False
) -> tuple[list[str], list[str]]:
    cflags: list[str] = []
    ldflags: list[str] = []

    should_use_optimized_flags = not (
        config.aot_inductor.debug_compile
        or os.environ.get("TORCHINDUCTOR_DEBUG_COMPILE", "0") == "1"
    )
    should_add_debug_symbol_flags = (
        config.aot_inductor.debug_compile
        or config.aot_inductor.debug_symbols
        or os.environ.get("TORCHINDUCTOR_DEBUG_COMPILE", "0") == "1"
        or os.environ.get("TORCHINDUCTOR_DEBUG_SYMBOL", "0") == "1"
    )
    if should_use_optimized_flags:
        if _IS_WINDOWS:
            cflags += ["O1" if min_optimize else "O2"]
        else:
            cflags += [
                config.aot_inductor.compile_wrapper_opt_level if min_optimize else "O3",
                "DNDEBUG",
            ]
    else:
        if _IS_WINDOWS:
            cflags += ["Od", "Ob0", "Oy-"]
        else:
            cflags += ["O0"]

    if should_add_debug_symbol_flags:
        debug_cflags, debug_ldflags = _get_inductor_debug_symbol_cflags()
        cflags += debug_cflags
        ldflags += debug_ldflags

    if config.aot_inductor.enable_frame_pointer:
        if _IS_WINDOWS:
            cflags.append("Oy-")
        else:
            cflags.append("fno-omit-frame-pointer")

    cflags += _get_ffast_math_flags()

    if _IS_WINDOWS:
        pass
    else:
        if sys.platform != "darwin":
            # on macos, unknown argument: '-fno-tree-loop-vectorize'
            if _is_gcc(cpp_compiler):
                cflags.append("fno-tree-loop-vectorize")
            # https://stackoverflow.com/questions/65966969/why-does-march-native-not-work-on-apple-m1
            # `-march=native` is unrecognized option on M1
            if not config.is_fbcode():
                if platform.machine() == "ppc64le":
                    cflags.append("mcpu=native")
                elif platform.machine() == "riscv64":
                    cflags.append("march=rv64gc")
                elif platform.machine() == "riscv32":
                    cflags.append("march=rv32gc")
                else:
                    cflags.append("march=native")

        if config.aot_inductor.enable_lto and _is_clang(cpp_compiler):
            cflags.append("flto=thin")

    return cflags, ldflags