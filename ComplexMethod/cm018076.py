def test_ensure_single_execution_file_not_unlinked(tmp_path: Path) -> None:
    """Test that lock file is never unlinked to avoid race conditions."""
    config_dir = str(tmp_path)
    lock_file_path = tmp_path / runner.LOCK_FILE_NAME

    # First run creates the lock file
    with runner.ensure_single_execution(config_dir) as lock:
        assert lock.exit_code is None
        assert lock_file_path.exists()
        # Get inode to verify it's the same file
        stat1 = lock_file_path.stat()

    # After context exit, file should still exist
    assert lock_file_path.exists()
    stat2 = lock_file_path.stat()
    # Verify it's the exact same file (same inode)
    assert stat1.st_ino == stat2.st_ino

    # Second run should reuse the same file
    with runner.ensure_single_execution(config_dir) as lock:
        assert lock.exit_code is None
        assert lock_file_path.exists()
        stat3 = lock_file_path.stat()
        # Still the same file (not recreated)
        assert stat1.st_ino == stat3.st_ino

    # After second run, still the same file
    assert lock_file_path.exists()
    stat4 = lock_file_path.stat()
    assert stat1.st_ino == stat4.st_ino