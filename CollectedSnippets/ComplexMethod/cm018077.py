def test_ensure_single_execution_sequential_runs(tmp_path: Path) -> None:
    """Test that sequential runs work correctly after lock is released."""
    config_dir = str(tmp_path)
    lock_file_path = tmp_path / runner.LOCK_FILE_NAME

    with runner.ensure_single_execution(config_dir) as lock:
        assert lock.exit_code is None
        assert lock_file_path.exists()
        with open(lock_file_path, encoding="utf-8") as f:
            first_data = json.load(f)

    # Lock file should still exist after first run (not unlinked)
    assert lock_file_path.exists()

    # Small delay to ensure different timestamp
    time.sleep(0.00001)

    with runner.ensure_single_execution(config_dir) as lock:
        assert lock.exit_code is None
        assert lock_file_path.exists()
        with open(lock_file_path, encoding="utf-8") as f:
            second_data = json.load(f)
            assert second_data["pid"] == os.getpid()
            assert second_data["start_ts"] > first_data["start_ts"]

    # Lock file should still exist after second run (not unlinked)
    assert lock_file_path.exists()