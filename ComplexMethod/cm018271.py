async def test_wait_integration_startup(
    hass: HomeAssistant,
    hass_storage: dict[str, Any],
    hass_client: ClientSessionGenerator,
) -> None:
    """Test we can get wait for an integration to load during startup."""
    mock_storage(hass_storage, {"done": []})

    assert await async_setup_component(hass, "onboarding", {})
    await hass.async_block_till_done()
    client = await hass_client()

    setup_stall = asyncio.Event()
    setup_started = asyncio.Event()

    async def mock_setup(hass: HomeAssistant, _) -> bool:
        setup_started.set()
        await setup_stall.wait()
        return True

    mock_integration(hass, MockModule("test", async_setup=mock_setup))

    # The integration is not loaded, and is also not scheduled to load
    req = await client.post("/api/onboarding/integration/wait", json={"domain": "test"})
    assert req.status == HTTPStatus.OK
    data = await req.json()
    assert data == {"integration_loaded": False}

    # Mark the component as scheduled to be loaded
    async_set_domains_to_be_loaded(hass, {"test"})

    # Start loading the component, including its config entries
    hass.async_create_task(async_setup_component(hass, "test", {}))
    await setup_started.wait()

    # The component is not yet loaded
    assert "test" not in hass.config.components

    # Allow setup to proceed
    setup_stall.set()

    # The component is scheduled to load, this will block until the config entry is loaded
    req = await client.post("/api/onboarding/integration/wait", json={"domain": "test"})
    assert req.status == HTTPStatus.OK
    data = await req.json()
    assert data == {"integration_loaded": True}

    # The component has been loaded
    assert "test" in hass.config.components