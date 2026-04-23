def test_battery_icon() -> None:
    """Test icon generator for battery sensor."""
    assert icon.icon_for_battery_level(None, True) == "mdi:battery-unknown"
    assert icon.icon_for_battery_level(None, False) == "mdi:battery-unknown"

    assert icon.icon_for_battery_level(5, True) == "mdi:battery-outline"
    assert icon.icon_for_battery_level(5, False) == "mdi:battery-alert"

    assert icon.icon_for_battery_level(100, True) == "mdi:battery-charging-100"
    assert icon.icon_for_battery_level(100, False) == "mdi:battery"

    iconbase = "mdi:battery"
    for level in range(0, 100, 5):
        print(  # noqa: T201
            f"Level: {level}. icon: {icon.icon_for_battery_level(level, False)}, "
            f"charging: {icon.icon_for_battery_level(level, True)}"
        )
        if level <= 10:
            postfix_charging = "-outline"
        elif level <= 30:
            postfix_charging = "-charging-20"
        elif level <= 50:
            postfix_charging = "-charging-40"
        elif level <= 70:
            postfix_charging = "-charging-60"
        elif level <= 90:
            postfix_charging = "-charging-80"
        else:
            postfix_charging = "-charging-100"
        if 5 < level < 95:
            postfix = f"-{int(round(level / 10 - 0.01)) * 10}"
        elif level <= 5:
            postfix = "-alert"
        else:
            postfix = ""
        assert iconbase + postfix == icon.icon_for_battery_level(level, False)
        assert iconbase + postfix_charging == icon.icon_for_battery_level(level, True)