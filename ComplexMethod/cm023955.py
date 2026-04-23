async def test_service_get_diskspace_multiple_drives(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_sonarr: MagicMock,
) -> None:
    """Test get_diskspace service with multiple drives."""
    # Mock multiple disks response
    mock_sonarr.async_get_diskspace.return_value = [
        Diskspace(
            {
                "path": "C:\\",
                "label": "System",
                "freeSpace": 100000000000,
                "totalSpace": 500000000000,
            }
        ),
        Diskspace(
            {
                "path": "D:\\Media",
                "label": "Media Storage",
                "freeSpace": 2000000000000,
                "totalSpace": 4000000000000,
            }
        ),
        Diskspace(
            {
                "path": "/mnt/nas",
                "label": "NAS",
                "freeSpace": 10000000000000,
                "totalSpace": 20000000000000,
            }
        ),
    ]

    response = await hass.services.async_call(
        DOMAIN,
        SERVICE_GET_DISKSPACE,
        {ATTR_ENTRY_ID: init_integration.entry_id},
        blocking=True,
        return_response=True,
    )

    assert response is not None
    assert ATTR_DISKS in response
    disks = response[ATTR_DISKS]
    assert isinstance(disks, dict)
    assert len(disks) == 3

    # Check first disk (C:\)
    c_drive = disks["C:\\"]
    assert c_drive["path"] == "C:\\"
    assert c_drive["label"] == "System"
    assert c_drive["free_space"] == 100000000000
    assert c_drive["total_space"] == 500000000000
    assert c_drive["unit"] == "bytes"

    # Check second disk (D:\Media)
    d_drive = disks["D:\\Media"]
    assert d_drive["path"] == "D:\\Media"
    assert d_drive["label"] == "Media Storage"
    assert d_drive["free_space"] == 2000000000000
    assert d_drive["total_space"] == 4000000000000

    # Check third disk (/mnt/nas)
    nas = disks["/mnt/nas"]
    assert nas["path"] == "/mnt/nas"
    assert nas["label"] == "NAS"
    assert nas["free_space"] == 10000000000000
    assert nas["total_space"] == 20000000000000