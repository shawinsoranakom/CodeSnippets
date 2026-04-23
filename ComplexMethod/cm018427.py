async def test_attributes(hass: HomeAssistant) -> None:
    """Test the attributes."""
    number = MockDefaultNumberEntity()
    number.hass = hass
    assert number.max_value == 100.0
    assert number.min_value == 0.0
    assert number.step == 1.0
    assert number.unit_of_measurement is None
    assert number.value == 0.5
    assert number.capability_attributes == {
        ATTR_MAX: 100.0,
        ATTR_MIN: 0.0,
        ATTR_MODE: NumberMode.AUTO,
        ATTR_STEP: 1.0,
    }

    number_2 = MockNumberEntity()
    number_2.hass = hass
    assert number_2.max_value == 0.5
    assert number_2.min_value == -0.5
    assert number_2.step == 0.1
    assert number_2.unit_of_measurement == "native_cats"
    assert number_2.value == 0.5
    assert number_2.capability_attributes == {
        ATTR_MAX: 0.5,
        ATTR_MIN: -0.5,
        ATTR_MODE: NumberMode.AUTO,
        ATTR_STEP: 0.1,
    }

    number_3 = MockNumberEntityAttr()
    number_3.hass = hass
    assert number_3.max_value == 1000.0
    assert number_3.min_value == -1000.0
    assert number_3.step == 100.0
    assert number_3.unit_of_measurement == "native_dogs"
    assert number_3.value == 500.0
    assert number_3.capability_attributes == {
        ATTR_MAX: 1000.0,
        ATTR_MIN: -1000.0,
        ATTR_MODE: NumberMode.AUTO,
        ATTR_STEP: 100.0,
    }

    number_4 = MockNumberEntityDescr()
    number_4.hass = hass
    assert number_4.max_value == 10.0
    assert number_4.min_value == -10.0
    assert number_4.step == 2.0
    assert number_4.unit_of_measurement == "native_rabbits"
    assert number_4.value is None
    assert number_4.capability_attributes == {
        ATTR_MAX: 10.0,
        ATTR_MIN: -10.0,
        ATTR_MODE: NumberMode.AUTO,
        ATTR_STEP: 2.0,
    }

    number_5 = MockNumberEntityAttrWithDescription()
    number_5.hass = hass
    assert number_5.max_value == 1000.0
    assert number_5.min_value == -1000.0
    assert number_5.step == 100.0
    assert number_5.native_step == 100.0
    assert number_5.unit_of_measurement == "native_dogs"
    assert number_5.value == 500.0
    assert number_5.capability_attributes == {
        ATTR_MAX: 1000.0,
        ATTR_MIN: -1000.0,
        ATTR_MODE: NumberMode.AUTO,
        ATTR_STEP: 100.0,
    }