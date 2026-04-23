def test_restore_backup(
    backup: str,
    password: str | None,
    restore_backup_content: backup_restore.RestoreBackupFileContent,
    expected_kept_files: set[str],
    expected_restored_files: set[str],
    expected_directories_after_restore: set[str],
    tmp_path: Path,
) -> None:
    """Test restoring a backup.

    This includes checking that expected files are kept, restored, and
    that we are cleaning up the current configuration directory.
    """
    backup_file_path = tmp_path / "backups" / "test.tar"

    def get_files(path: Path) -> set[str]:
        """Get all files under path."""
        return {str(f.relative_to(path)) for f in path.rglob("*")}

    existing_dirs = {
        "backups",
        "tmp_backups",
        "www",
    }
    existing_files = {
        ".HA_RESTORE",
        ".HA_VERSION",
        "home-assistant_v2.db",
        "home-assistant_v2.db-wal",
    }

    for d in existing_dirs:
        (tmp_path / d).mkdir(exist_ok=True)
    for f in existing_files:
        (tmp_path / f).write_text("before_restore")

    get_fixture_path(f"core/backup_restore/{backup}", None).copy(backup_file_path)

    files_before_restore = get_files(tmp_path)
    assert files_before_restore == {
        ".HA_RESTORE",
        ".HA_VERSION",
        "backups",
        "backups/test.tar",
        "home-assistant_v2.db",
        "home-assistant_v2.db-wal",
        "tmp_backups",
        "www",
    }
    kept_files_data = {}
    for file in expected_kept_files:
        kept_files_data[file] = (tmp_path / file).read_bytes()

    restore_backup_content.backup_file_path = backup_file_path
    restore_backup_content.password = password

    with (
        mock.patch(
            "homeassistant.backup_restore.restore_backup_file_content",
            return_value=restore_backup_content,
        ),
    ):
        assert backup_restore.restore_backup(tmp_path.as_posix()) is True

    files_after_restore = get_files(tmp_path)
    assert (
        files_after_restore
        == {".HA_RESTORE_RESULT"}
        | expected_kept_files
        | expected_restored_files
        | expected_directories_after_restore
    )

    for d in expected_directories_after_restore:
        assert (tmp_path / d).is_dir()
    for file in expected_kept_files:
        assert (tmp_path / file).read_bytes() == kept_files_data[file]
    for file in expected_restored_files:
        assert (tmp_path / file).read_bytes() == b"restored_from_backup"

    assert restore_result_file_content(tmp_path) == {
        "error": None,
        "error_type": None,
        "success": True,
    }