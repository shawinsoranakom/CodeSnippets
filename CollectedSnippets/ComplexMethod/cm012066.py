def _ensure_mingw_cudart_import_lib(libraries_dirs: list[str]) -> list[str]:
    """
    Auto-generate a MinGW-compatible import library (libcudart.a)
    from the CUDA runtime DLL. This avoids linking against the hybrid cudart.lib
    which contains MSVC-compiled static objects with /GS security symbols that
    MinGW cannot resolve.

    Falls back to creating MSVC GS security stubs if the DLL is unavailable,
    and falls back gracefully to the original cudart.lib if that also fails.

    Returns a list of extra library names to link (e.g. ["msvc_gs_stubs"]).
    """
    import glob

    windows_cuda_home = os.environ.get("WINDOWS_CUDA_HOME")
    if not windows_cuda_home:
        log.debug(
            "WINDOWS_CUDA_HOME not set, skipping MinGW cudart import lib generation"
        )
        return []

    for lib_dir in libraries_dirs:
        if os.path.exists(os.path.join(lib_dir, "libcudart.a")):
            log.debug("libcudart.a already exists in %s, skipping generation", lib_dir)
            return []

    # Find the CUDA runtime DLL for import lib generation
    bin_dir = os.path.join(windows_cuda_home, "bin", "x64")
    if not os.path.isdir(bin_dir):
        bin_dir = os.path.join(windows_cuda_home, "bin")
    dll_candidates = glob.glob(os.path.join(bin_dir, "cudart64_*.dll"))

    # Find a writable directory containing cudart.lib for output
    output_dir = None
    for lib_dir in libraries_dirs:
        if os.path.isdir(lib_dir) and os.access(lib_dir, os.W_OK):
            if os.path.exists(os.path.join(lib_dir, "cudart.lib")):
                output_dir = lib_dir
                break

    if not dll_candidates:
        log.warning(
            "No cudart64_*.dll found in %s. Cannot generate MinGW import library. "
            "Will create MSVC GS security stubs as fallback.",
            bin_dir,
        )
        # Fallback: create GS stubs so the hybrid cudart.lib can link
        if output_dir is not None:
            stub_lib = _create_msvc_gs_stubs_lib(output_dir)
            if stub_lib:
                return [stub_lib]
        return []

    if output_dir is None:
        log.warning(
            "No writable directory containing cudart.lib found. "
            "Cannot generate MinGW import library. "
            "If linking fails with undefined references to __security_cookie, "
            "ensure cudart.lib is present in one of: %s",
            libraries_dirs,
        )
        return []

    dll_path = dll_candidates[0]
    dll_name = os.path.basename(dll_path)

    def_path = os.path.join(output_dir, dll_name.replace(".dll", ".def"))
    import_lib_path = os.path.join(output_dir, "libcudart.a")

    try:
        _gen_mingw_import_lib(dll_path, def_path, import_lib_path)
        return []
    except (FileNotFoundError, subprocess.CalledProcessError):
        log.warning(
            "Failed to generate MinGW cudart import library. "
            "Falling back to MSVC GS stubs.",
            exc_info=True,
        )
        for f in [def_path, import_lib_path]:
            if os.path.exists(f):
                os.remove(f)
        # Fallback: create GS stubs
        stub_lib = _create_msvc_gs_stubs_lib(output_dir)
        if stub_lib:
            return [stub_lib]
        return []