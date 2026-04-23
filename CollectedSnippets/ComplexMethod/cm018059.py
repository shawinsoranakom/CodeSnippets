def test_integration_properties(hass: HomeAssistant) -> None:
    """Test integration properties."""
    integration = loader.Integration(
        hass,
        "homeassistant.components.hue",
        None,
        {
            "name": "Philips Hue",
            "domain": "hue",
            "dependencies": ["test-dep"],
            "requirements": ["test-req==1.0.0"],
            "zeroconf": ["_hue._tcp.local."],
            "homekit": {"models": ["BSB002"]},
            "dhcp": [
                {"hostname": "tesla_*", "macaddress": "4CFCAA*"},
                {"hostname": "tesla_*", "macaddress": "044EAF*"},
                {"hostname": "tesla_*", "macaddress": "98ED5C*"},
                {"registered_devices": True},
            ],
            "bluetooth": [{"manufacturer_id": 76, "manufacturer_data_start": [0x06]}],
            "usb": [
                {"vid": "10C4", "pid": "EA60"},
                {"vid": "1CF1", "pid": "0030"},
                {"vid": "1A86", "pid": "7523"},
                {"vid": "10C4", "pid": "8A2A"},
            ],
            "ssdp": [
                {
                    "manufacturer": "Royal Philips Electronics",
                    "modelName": "Philips hue bridge 2012",
                },
                {
                    "manufacturer": "Royal Philips Electronics",
                    "modelName": "Philips hue bridge 2015",
                },
                {"manufacturer": "Signify", "modelName": "Philips hue bridge 2015"},
            ],
            "mqtt": ["hue/discovery"],
            "version": "1.0.0",
            "quality_scale": "gold",
        },
    )
    assert integration.name == "Philips Hue"
    assert integration.domain == "hue"
    assert integration.homekit == {"models": ["BSB002"]}
    assert integration.zeroconf == ["_hue._tcp.local."]
    assert integration.dhcp == [
        {"hostname": "tesla_*", "macaddress": "4CFCAA*"},
        {"hostname": "tesla_*", "macaddress": "044EAF*"},
        {"hostname": "tesla_*", "macaddress": "98ED5C*"},
        {"registered_devices": True},
    ]
    assert integration.usb == [
        {"vid": "10C4", "pid": "EA60"},
        {"vid": "1CF1", "pid": "0030"},
        {"vid": "1A86", "pid": "7523"},
        {"vid": "10C4", "pid": "8A2A"},
    ]
    assert integration.bluetooth == [
        {"manufacturer_id": 76, "manufacturer_data_start": [0x06]}
    ]
    assert integration.ssdp == [
        {
            "manufacturer": "Royal Philips Electronics",
            "modelName": "Philips hue bridge 2012",
        },
        {
            "manufacturer": "Royal Philips Electronics",
            "modelName": "Philips hue bridge 2015",
        },
        {"manufacturer": "Signify", "modelName": "Philips hue bridge 2015"},
    ]
    assert integration.mqtt == ["hue/discovery"]
    assert integration.dependencies == ["test-dep"]
    assert integration.requirements == ["test-req==1.0.0"]
    assert integration.is_built_in is True
    assert integration.overwrites_built_in is False
    assert integration.version == "1.0.0"
    assert integration.quality_scale == "gold"

    integration = loader.Integration(
        hass,
        "custom_components.hue",
        None,
        {
            "name": "Philips Hue",
            "domain": "hue",
            "dependencies": ["test-dep"],
            "requirements": ["test-req==1.0.0"],
            "quality_scale": "gold",
        },
    )
    assert integration.is_built_in is False
    assert integration.overwrites_built_in is True
    assert integration.homekit is None
    assert integration.zeroconf is None
    assert integration.dhcp is None
    assert integration.bluetooth is None
    assert integration.usb is None
    assert integration.ssdp is None
    assert integration.mqtt is None
    assert integration.version is None
    assert integration.quality_scale == "custom"

    integration = loader.Integration(
        hass,
        "custom_components.hue",
        None,
        {
            "name": "Philips Hue",
            "domain": "hue",
            "dependencies": ["test-dep"],
            "zeroconf": [{"type": "_hue._tcp.local.", "name": "hue*"}],
            "requirements": ["test-req==1.0.0"],
        },
    )
    assert integration.is_built_in is False
    assert integration.overwrites_built_in is True
    assert integration.homekit is None
    assert integration.zeroconf == [{"type": "_hue._tcp.local.", "name": "hue*"}]
    assert integration.dhcp is None
    assert integration.usb is None
    assert integration.bluetooth is None
    assert integration.ssdp is None