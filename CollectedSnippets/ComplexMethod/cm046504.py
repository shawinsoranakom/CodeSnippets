def test_live_rss_matches_kernel_vmrss(tmp_path):
    """Spawn a real child, let it allocate real bytes, confirm
    ``bytes_loaded`` tracks the kernel's VmRSS within a sane tolerance."""
    # Child that allocates ~100 MB of zero'd bytes and then idles.
    script = tmp_path / "burn.py"
    script.write_text(
        "import time, sys\n"
        "buf = bytearray(100 * 1024 * 1024)\n"  # 100 MB
        "# touch every page so RSS actually grows\n"
        "for i in range(0, len(buf), 4096):\n"
        "    buf[i] = 1\n"
        "sys.stdout.write('ready\\n')\n"
        "sys.stdout.flush()\n"
        "time.sleep(10)\n"
    )
    proc = subprocess.Popen(
        [sys.executable, str(script)],
        stdout = subprocess.PIPE,
        stderr = subprocess.PIPE,
    )
    try:
        # Wait for the child to finish touching pages.
        ready = proc.stdout.readline()
        assert ready.strip() == b"ready"

        # Create a fake 200 MB sparse gguf so bytes_total is concrete.
        gguf = tmp_path / "model.gguf"
        with open(gguf, "wb") as f:
            f.truncate(200 * 1024 * 1024)

        inst = _make_backend(proc.pid, str(gguf), healthy = False)
        out = inst.load_progress()

        assert out is not None, "load_progress returned None for live pid"
        assert out["phase"] == "mmap"
        assert out["bytes_total"] == 200 * 1024 * 1024
        # VmRSS for the Python child includes the interpreter + the 100MB
        # buffer, so a realistic floor is 50 MB and ceiling is 200 MB.
        assert (
            out["bytes_loaded"] >= 50 * 1024 * 1024
        ), f"bytes_loaded unexpectedly low: {out['bytes_loaded']}"
        assert out["bytes_loaded"] <= 200 * 1024 * 1024
        assert 0.0 < out["fraction"] <= 1.0
    finally:
        proc.terminate()
        try:
            proc.wait(timeout = 5)
        except subprocess.TimeoutExpired:
            proc.kill()