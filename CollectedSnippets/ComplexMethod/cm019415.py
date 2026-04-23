async def test_migrate_from_version_1_to_2(
    hass: HomeAssistant,
    get_data: MockRestData,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    snapshot: SnapshotAssertion,
) -> None:
    """Test migration from version 1.1 to 2.1 with config subentries."""

    @dataclass(frozen=True, kw_only=True)
    class MockConfigSubentry(ConfigSubentry):
        """Container for a configuration subentry."""

        subentry_id: str = "01JZQ1G63X2DX66GZ9ZTFY9PEH"

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        source=SOURCE_USER,
        options={
            "encoding": "UTF-8",
            "method": "GET",
            "resource": "http://www.home-assistant.io",
            "username": "user",
            "password": "pass",
            "sensor": [
                {
                    "index": 0,
                    "name": "Current version",
                    "select": ".release-date",
                    "unique_id": "a0bde946-5c96-11f0-b55f-0242ac110002",
                    "value_template": "{{ value }}",
                }
            ],
            "timeout": 10.0,
            "verify_ssl": True,
        },
        entry_id="01JZN04ZJ9BQXXGXDS05WS7D6P",
        version=1,
    )
    config_entry.add_to_hass(hass)
    device = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        entry_type=dr.DeviceEntryType.SERVICE,
        identifiers={(DOMAIN, "a0bde946-5c96-11f0-b55f-0242ac110002")},
        manufacturer="Scrape",
        name="Current version",
    )
    entity_registry.async_get_or_create(
        SENSOR_DOMAIN,
        DOMAIN,
        "a0bde946-5c96-11f0-b55f-0242ac110002",
        config_entry=config_entry,
        device_id=device.id,
        original_name="Current version",
        has_entity_name=True,
        suggested_object_id="current_version",
    )
    assert hass.config_entries.async_get_entry(config_entry.entry_id) == snapshot(
        name="pre_migration_config_entry"
    )
    with (
        patch(
            "homeassistant.components.rest.RestData",
            return_value=get_data,
        ),
        patch("homeassistant.components.scrape.ConfigSubentry", MockConfigSubentry),
    ):
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done(wait_background_tasks=True)

    assert config_entry.state is ConfigEntryState.LOADED

    assert hass.config_entries.async_get_entry(config_entry.entry_id) == snapshot(
        name="post_migration_config_entry"
    )
    device = device_registry.async_get(device.id)
    assert device == snapshot(name="device_registry")
    entity = entity_registry.async_get("sensor.current_version")
    assert entity == snapshot(name="entity_registry")

    assert config_entry.subentries == {
        "01JZQ1G63X2DX66GZ9ZTFY9PEH": MockConfigSubentry(
            data={
                "advanced": {"value_template": "{{ value }}"},
                "index": 0,
                "select": ".release-date",
            },
            subentry_id="01JZQ1G63X2DX66GZ9ZTFY9PEH",
            subentry_type="entity",
            title="Current version",
            unique_id=None,
        ),
    }
    assert device.config_entries == {"01JZN04ZJ9BQXXGXDS05WS7D6P"}
    assert device.config_entries_subentries == {
        "01JZN04ZJ9BQXXGXDS05WS7D6P": {
            "01JZQ1G63X2DX66GZ9ZTFY9PEH",
        },
    }
    assert entity.config_entry_id == config_entry.entry_id
    assert entity.config_subentry_id == "01JZQ1G63X2DX66GZ9ZTFY9PEH"

    state = hass.states.get("sensor.current_version")
    assert state.state == "January 17, 2022"