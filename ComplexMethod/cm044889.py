def _has_working_bash() -> bool:
    """Check whether a functional native bash is available.

    On Windows, ``subprocess.run(["bash", ...])`` uses CreateProcess,
    which searches System32 *before* PATH — so it may find the WSL
    launcher even when Git-for-Windows bash appears first in PATH via
    ``shutil.which``.  We therefore probe with bare ``"bash"`` (the
    same way test helpers invoke it) to get an accurate result.

    On Windows, only Git-for-Windows bash (MSYS2/MINGW) is accepted.
    The WSL launcher is rejected because it runs in a separate Linux
    filesystem and cannot handle native Windows paths used by the
    test fixtures.

    Set SPECKIT_TEST_BASH=1 to force-enable bash tests regardless.
    """
    if os.environ.get("SPECKIT_TEST_BASH") == "1":
        return True
    if shutil.which("bash") is None:
        return False
    # Probe with bare "bash" — same as the test helpers — so that
    # Windows CreateProcess resolution order is respected.
    try:
        r = subprocess.run(
            ["bash", "-c", "echo ok"],
            capture_output=True, text=True, timeout=5,
        )
        if r.returncode != 0 or "ok" not in r.stdout:
            return False
    except (OSError, subprocess.TimeoutExpired):
        return False
    # On Windows, verify we have MSYS/MINGW bash (Git for Windows),
    # not the WSL launcher which can't handle native paths.
    if sys.platform == "win32":
        try:
            u = subprocess.run(
                ["bash", "-c", "uname -s"],
                capture_output=True, text=True, timeout=5,
            )
            kernel = u.stdout.strip().upper()
            if not any(k in kernel for k in ("MSYS", "MINGW", "CYGWIN")):
                return False
        except (OSError, subprocess.TimeoutExpired):
            return False
    return True