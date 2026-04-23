async def test_fixtures_valid(hass: HomeAssistant) -> None:
    """Ensure Tuya fixture files are valid."""
    # We want to ensure that the fixture files do not contain
    # `home_assistant`, `id`, or `terminal_id` keys.
    # These are provided by the Tuya diagnostics and should be removed
    # from the fixture.
    EXCLUDE_KEYS = ("home_assistant", "id", "terminal_id")

    for device_code in DEVICE_MOCKS:
        details = await async_load_json_object_fixture(
            hass, f"{device_code}.json", DOMAIN
        )
        for key in EXCLUDE_KEYS:
            assert key not in details, (
                f"Please remove data[`'{key}']` from {device_code}.json"
            )
        if "status" in details:
            statuses = details["status"]
            for key in statuses:
                if key in _REDACTED_DPCODES:
                    assert statuses[key] == "**REDACTED**", (
                        f"Please mark `data['status']['{key}']` as `**REDACTED**`"
                        f" in {device_code}.json"
                    )