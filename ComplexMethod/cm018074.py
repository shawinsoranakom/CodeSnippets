def test_ensure_single_execution_success(tmp_path: Path) -> None:
    """Test successful single instance execution."""
    config_dir = str(tmp_path)
    lock_file_path = tmp_path / runner.LOCK_FILE_NAME

    with runner.ensure_single_execution(config_dir) as lock:
        assert lock.exit_code is None
        assert lock_file_path.exists()

        with open(lock_file_path, encoding="utf-8") as f:
            data = json.load(f)
            assert data["pid"] == os.getpid()
            assert data["version"] == runner.LOCK_FILE_VERSION
            assert data["ha_version"] == __version__
            assert "start_ts" in data
            assert isinstance(data["start_ts"], float)

    # Lock file should still exist after context exit (we don't unlink to avoid races)
    assert lock_file_path.exists()