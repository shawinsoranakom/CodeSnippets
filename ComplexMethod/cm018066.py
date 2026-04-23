async def test_platforms_exists(hass: HomeAssistant) -> None:
    """Test platforms_exists."""
    original_os_listdir = os.listdir

    paths: list[str] = []

    def mock_list_dir(path: str) -> list[str]:
        paths.append(path)
        return original_os_listdir(path)

    with patch("homeassistant.loader.os.listdir", mock_list_dir):
        integration = await loader.async_get_integration(
            hass, "test_integration_platform"
        )
        assert integration.domain == "test_integration_platform"

    # Verify the files cache is primed
    assert integration.file_path in paths

    # component is loaded, should now return False
    with patch("homeassistant.loader.os.listdir", wraps=os.listdir) as mock_exists:
        component = integration.get_component()
    assert component.DOMAIN == "test_integration_platform"

    # The files cache should be primed when
    # the integration is resolved
    assert mock_exists.call_count == 0

    # component is loaded, should now return False
    with patch("homeassistant.loader.os.listdir", wraps=os.listdir) as mock_exists:
        assert integration.platforms_exists(("non_existing",)) == []

    # We should remember which files exist
    assert mock_exists.call_count == 0

    # component is loaded, should now return False
    with patch("homeassistant.loader.os.listdir", wraps=os.listdir) as mock_exists:
        assert integration.platforms_exists(("non_existing",)) == []

    # We should remember the file does not exist
    assert mock_exists.call_count == 0

    assert integration.platforms_exists(["group"]) == ["group"]

    platform = await integration.async_get_platform("group")
    assert platform.MAGIC == 1

    platform = integration.get_platform("group")
    assert platform.MAGIC == 1

    assert integration.platforms_exists(["group"]) == ["group"]

    assert integration.platforms_are_loaded(["group"]) is True
    assert integration.platforms_are_loaded(["other"]) is False