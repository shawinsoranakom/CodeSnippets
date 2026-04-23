async def test_energystorage_vacuum(hass: HomeAssistant) -> None:
    """Test EnergyStorage trait support for vacuum domain."""
    assert helpers.get_google_type(vacuum.DOMAIN, None) is not None
    assert trait.EnergyStorageTrait.supported(
        vacuum.DOMAIN, VacuumEntityFeature.BATTERY, None, None
    )

    trt = trait.EnergyStorageTrait(
        hass,
        State(
            "vacuum.bla",
            vacuum.VacuumActivity.DOCKED,
            {
                ATTR_SUPPORTED_FEATURES: VacuumEntityFeature.BATTERY,
                ATTR_BATTERY_LEVEL: 100,
            },
        ),
        BASIC_CONFIG,
    )

    assert trt.sync_attributes() == {
        "isRechargeable": True,
        "queryOnlyEnergyStorage": True,
    }

    assert trt.query_attributes() == {
        "descriptiveCapacityRemaining": "FULL",
        "capacityRemaining": [{"rawValue": 100, "unit": "PERCENTAGE"}],
        "capacityUntilFull": [{"rawValue": 0, "unit": "PERCENTAGE"}],
        "isCharging": True,
        "isPluggedIn": True,
    }

    trt = trait.EnergyStorageTrait(
        hass,
        State(
            "vacuum.bla",
            vacuum.VacuumActivity.CLEANING,
            {
                ATTR_SUPPORTED_FEATURES: VacuumEntityFeature.BATTERY,
                ATTR_BATTERY_LEVEL: 20,
            },
        ),
        BASIC_CONFIG,
    )

    assert trt.sync_attributes() == {
        "isRechargeable": True,
        "queryOnlyEnergyStorage": True,
    }

    assert trt.query_attributes() == {
        "descriptiveCapacityRemaining": "CRITICALLY_LOW",
        "capacityRemaining": [{"rawValue": 20, "unit": "PERCENTAGE"}],
        "capacityUntilFull": [{"rawValue": 80, "unit": "PERCENTAGE"}],
        "isCharging": False,
        "isPluggedIn": False,
    }

    with pytest.raises(helpers.SmartHomeError) as err:
        await trt.execute(trait.COMMAND_CHARGE, BASIC_DATA, {"charge": True}, {})
    assert err.value.code == const.ERR_FUNCTION_NOT_SUPPORTED

    with pytest.raises(helpers.SmartHomeError) as err:
        await trt.execute(trait.COMMAND_CHARGE, BASIC_DATA, {"charge": False}, {})
    assert err.value.code == const.ERR_FUNCTION_NOT_SUPPORTED