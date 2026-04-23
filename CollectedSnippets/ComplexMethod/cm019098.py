def test_human_readable_device_name() -> None:
    """Test human readable device name includes the passed data."""
    name = usb.human_readable_device_name(
        "/dev/null",
        "612020FD",
        "Silicon Labs",
        "HubZ Smart Home Controller - HubZ Z-Wave Com Port",
        "10C4",
        "8A2A",
    )
    assert "/dev/null" in name
    assert "612020FD" in name
    assert "Silicon Labs" in name
    assert "HubZ Smart Home Controller - HubZ Z-Wave Com Port"[:26] in name
    assert "10C4" in name
    assert "8A2A" in name

    name = usb.human_readable_device_name(
        "/dev/null",
        "612020FD",
        "Silicon Labs",
        None,
        "10C4",
        "8A2A",
    )
    assert "/dev/null" in name
    assert "612020FD" in name
    assert "Silicon Labs" in name
    assert "10C4" in name
    assert "8A2A" in name