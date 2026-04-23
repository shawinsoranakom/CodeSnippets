async def test_restore_entity_end_to_end(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    """Test restoring an entity end-to-end."""
    component_setup = Mock(return_value=True)

    setup_called = []

    entity_id = "test_domain.unnamed_device"
    data = async_get(hass)
    now = dt_util.utcnow()
    data.last_states = {
        entity_id: StoredState(State(entity_id, "stored"), None, now),
    }

    class MockRestoreEntity(RestoreEntity):
        """Mock restore entity."""

        def __init__(self) -> None:
            """Initialize the mock entity."""
            self._state: str | None = None

        @property
        def state(self) -> str | None:
            """Return the state."""
            return self._state

        async def async_added_to_hass(self) -> Coroutine[Any, Any, None]:
            """Run when entity about to be added to hass."""
            await super().async_added_to_hass()
            self._state = (await self.async_get_last_state()).state

    async def async_setup_platform(
        hass: HomeAssistant,
        config: ConfigType,
        async_add_entities: AddEntitiesCallback,
        discovery_info: DiscoveryInfoType | None = None,
    ) -> None:
        """Set up the test platform."""
        async_add_entities([MockRestoreEntity()])
        setup_called.append(True)

    mock_integration(hass, MockModule(DOMAIN, setup=component_setup))
    mock_integration(hass, MockModule(PLATFORM, dependencies=[DOMAIN]))

    platform = MockPlatform(async_setup_platform=async_setup_platform)
    mock_platform(hass, f"{PLATFORM}.{DOMAIN}", platform)

    component = EntityComponent(_LOGGER, DOMAIN, hass)

    await component.async_setup({DOMAIN: {"platform": PLATFORM, "sensors": None}})
    await hass.async_block_till_done()
    assert component_setup.called

    assert f"{PLATFORM}.{DOMAIN}" in hass.config.components
    assert len(setup_called) == 1

    platform = async_get_platform_without_config_entry(hass, PLATFORM, DOMAIN)
    assert platform.platform_name == PLATFORM
    assert platform.domain == DOMAIN
    assert hass.states.get(entity_id).state == "stored"

    await data.async_dump_states()
    await hass.async_block_till_done()

    storage_data = hass_storage[STORAGE_KEY]["data"]
    assert len(storage_data) == 1
    assert storage_data[0]["state"]["entity_id"] == entity_id
    assert storage_data[0]["state"]["state"] == "stored"

    await platform.async_reset()

    assert hass.states.get(entity_id) is None

    # Make sure the entity still gets saved to restore state
    # even though the platform has been reset since it should
    # not be expired yet.
    await data.async_dump_states()
    await hass.async_block_till_done()

    storage_data = hass_storage[STORAGE_KEY]["data"]
    assert len(storage_data) == 1
    assert storage_data[0]["state"]["entity_id"] == entity_id
    assert storage_data[0]["state"]["state"] == "stored"