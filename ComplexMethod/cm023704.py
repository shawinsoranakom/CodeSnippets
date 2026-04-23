def test_validate_or_move_away_sqlite_database(
    hass: HomeAssistant, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Ensure a malformed sqlite database is moved away."""
    test_dir = tmp_path.joinpath("test_validate_or_move_away_sqlite_database")
    test_dir.mkdir()
    test_db_file = f"{test_dir}/broken.db"
    dburl = f"{SQLITE_URL_PREFIX}{test_db_file}"

    assert util.validate_sqlite_database(test_db_file) is False
    assert os.path.exists(test_db_file) is True
    assert util.validate_or_move_away_sqlite_database(dburl) is False

    corrupt_db_file(test_db_file)

    assert util.validate_sqlite_database(dburl) is False

    assert util.validate_or_move_away_sqlite_database(dburl) is False

    assert "corrupt or malformed" in caplog.text

    assert util.validate_sqlite_database(dburl) is False

    assert util.validate_or_move_away_sqlite_database(dburl) is True