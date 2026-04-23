def comfy_url_and_proc(comfy_tmp_base_dir: Path, request: pytest.FixtureRequest):
    """
    Boot ComfyUI subprocess with:
      - sandbox base dir
      - file-backed sqlite DB in temp dir
      - autoscan disabled
    Returns (base_url, process, port)
    """
    port = _free_port()
    db_url = request.config.getoption("--db-url")
    if not db_url:
        # Use a file-backed sqlite database in the temp directory
        db_path = comfy_tmp_base_dir / "assets-test.sqlite3"
        db_url = f"sqlite:///{db_path}"

    logs_dir = comfy_tmp_base_dir / "logs"
    logs_dir.mkdir(exist_ok=True)
    out_log = open(logs_dir / "stdout.log", "w", buffering=1)
    err_log = open(logs_dir / "stderr.log", "w", buffering=1)

    comfy_root = Path(__file__).resolve().parent.parent.parent
    if not (comfy_root / "main.py").is_file():
        raise FileNotFoundError(f"main.py not found under {comfy_root}")

    proc = subprocess.Popen(
        args=[
            sys.executable,
            "main.py",
            f"--base-directory={str(comfy_tmp_base_dir)}",
            f"--database-url={db_url}",
            "--enable-assets",
            "--listen",
            "127.0.0.1",
            "--port",
            str(port),
            "--cpu",
        ],
        stdout=out_log,
        stderr=err_log,
        cwd=str(comfy_root),
        env={**os.environ},
    )

    for _ in range(50):
        if proc.poll() is not None:
            out_log.flush()
            err_log.flush()
            raise RuntimeError(f"ComfyUI exited early with code {proc.returncode}")
        time.sleep(0.1)

    base_url = f"http://127.0.0.1:{port}"
    try:
        with requests.Session() as s:
            _wait_http_ready(base_url, s, timeout=90.0)
        yield base_url, proc, port
    except Exception as e:
        with contextlib.suppress(Exception):
            proc.terminate()
            proc.wait(timeout=10)
        with contextlib.suppress(Exception):
            out_log.flush()
            err_log.flush()
        raise RuntimeError(f"ComfyUI did not become ready: {e}")

    if proc and proc.poll() is None:
        with contextlib.suppress(Exception):
            proc.terminate()
            proc.wait(timeout=15)
    out_log.close()
    err_log.close()