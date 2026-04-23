def _build_safe_env(workdir: str) -> dict[str, str]:
    """Build a minimal, credential-free environment for sandboxed subprocesses.

    Strips HF_TOKEN, WANDB_API_KEY, AWS_*, GH_TOKEN, LD_PRELOAD, DYLD_*, etc.
    Preserves the active Python interpreter and virtualenv directories in PATH
    so that pip, uv, and packages installed in the Studio runtime remain
    accessible.
    """
    # Start with the directory containing the running Python interpreter
    # so that subprocess calls to 'python', 'pip', etc. resolve to the
    # same environment the Studio server is running in.
    exe_dir = os.path.dirname(sys.executable)
    path_entries = [exe_dir] if exe_dir else []

    # If a virtualenv is active, include its bin/Scripts directory.
    venv = os.environ.get("VIRTUAL_ENV")
    if venv:
        venv_bin = os.path.join(venv, "Scripts" if sys.platform == "win32" else "bin")
        if venv_bin not in path_entries:
            path_entries.append(venv_bin)

    if sys.platform == "win32":
        sysroot = os.environ.get("SystemRoot", r"C:\Windows")
        path_entries.extend([os.path.join(sysroot, "System32"), sysroot])
    else:
        path_entries.extend(["/usr/local/bin", "/usr/bin", "/bin"])

    # Deduplicate while preserving order
    deduped = list(dict.fromkeys(p for p in path_entries if p))

    env = {
        "PATH": os.pathsep.join(deduped),
        "HOME": workdir,
        "TMPDIR": workdir,
        "LANG": os.environ.get("LANG", "C.UTF-8"),
        "TERM": "dumb",
        "PYTHONIOENCODING": "utf-8",
    }
    if venv:
        env["VIRTUAL_ENV"] = venv
    # Windows needs SystemRoot for Python/subprocess to work
    if sys.platform == "win32":
        env["SystemRoot"] = os.environ.get("SystemRoot", r"C:\Windows")
    return env