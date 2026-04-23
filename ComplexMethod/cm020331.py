async def test_media_migration(
    hass: HomeAssistant,
    setup_platform,
    legacy_media_path: str,
    media_path: str,
) -> None:
    """Test migration of media files from legacy path to new path."""
    legacy_path = pathlib.Path(legacy_media_path)
    cache_path = pathlib.Path(media_path)

    # Create some dummy files in the legacy path
    device_id = "device-1"
    legacy_device_path = legacy_path / device_id
    legacy_device_path.mkdir(parents=True)

    file1 = legacy_device_path / "event1.jpg"
    file1.write_text("content1")

    file2 = legacy_device_path / "event2.mp4"
    file2.write_text("content2")

    # Run setup (which triggers migration)
    await setup_platform()

    # Check if files are moved to cache path
    cache_device_path = cache_path / device_id
    assert (cache_device_path / "event1.jpg").exists()
    assert (cache_device_path / "event1.jpg").read_text() == "content1"
    assert (cache_device_path / "event2.mp4").exists()
    assert (cache_device_path / "event2.mp4").read_text() == "content2"

    # Check if files are removed from legacy path
    assert not file1.exists()
    assert not file2.exists()
    assert not legacy_device_path.exists()
    assert not legacy_path.exists()