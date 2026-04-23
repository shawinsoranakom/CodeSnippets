def test_ensure_single_execution_blocked(
    tmp_path: Path, capfd: pytest.CaptureFixture[str]
) -> None:
    """Test that second instance is blocked when lock exists."""
    config_dir = str(tmp_path)
    lock_file_path = tmp_path / runner.LOCK_FILE_NAME

    # Create and lock the file to simulate another instance
    with open(lock_file_path, "w+", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

        instance_info = {
            "pid": 12345,
            "version": 1,
            "ha_version": "2025.1.0",
            "start_ts": time.time() - 3600,  # Started 1 hour ago
        }
        json.dump(instance_info, lock_file)
        lock_file.flush()

        with runner.ensure_single_execution(config_dir) as lock:
            assert lock.exit_code == 1

        captured = capfd.readouterr()
        assert "Another Home Assistant instance is already running!" in captured.err
        assert "PID: 12345" in captured.err
        assert "Version: 2025.1.0" in captured.err
        assert "Started: " in captured.err
        # Should show local time since naive datetime
        assert "(local time)" in captured.err
        assert f"Config directory: {config_dir}" in captured.err