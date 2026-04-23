def test_web_dashboard_spawn(tmp_path, tcp_port):
    metrics_dir = tmp_path / "metrics"
    metrics_dir.mkdir()
    # Create an empty metrics db file so dashboard can start
    db_file = metrics_dir / "metrics_empty.db"
    db_file.write_bytes(b"\x00")
    port = tcp_port
    env = os.environ.copy()
    env["PATHWAY_DETAILED_METRICS_DIR"] = str(metrics_dir)
    proc = subprocess.Popen(
        [
            "uvicorn",
            "pathway.web_dashboard.dashboard:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        env=env,
    )
    try:
        # Wait for server to start
        for _ in range(30):
            try:
                r = requests.get(f"http://127.0.0.1:{port}/")
                if r.status_code == 200:
                    break
            except Exception:
                time.sleep(0.5)
        else:
            pytest.fail("Dashboard did not start in time")
        # Check main page loads
        assert "<html" in r.text.lower()
        # Check API endpoint returns something
        r_api = requests.get(f"http://127.0.0.1:{port}/metrics/available_range")
        assert r_api.status_code == 200
        assert "min" in r_api.json()
        assert "max" in r_api.json()
    finally:
        proc.terminate()
        proc.wait()