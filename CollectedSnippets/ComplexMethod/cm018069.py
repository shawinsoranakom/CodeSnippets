async def test_async_get_integrations_multiple_non_existent(
    hass: HomeAssistant,
) -> None:
    """Test async_get_integrations with multiple non-existent integrations."""
    integrations = await loader.async_get_integrations(hass, ["does_not_exist"])
    assert isinstance(integrations["does_not_exist"], loader.IntegrationNotFound)

    async def slow_load_failure(
        *args: Any, **kwargs: Any
    ) -> dict[str, loader.Integration]:
        await asyncio.sleep(0.1)
        return {}

    with patch.object(hass, "async_add_executor_job", slow_load_failure):
        task1 = hass.async_create_task(
            loader.async_get_integrations(hass, ["does_not_exist", "does_not_exist2"])
        )
        # Task one should now be waiting for executor job
    task2 = hass.async_create_task(
        loader.async_get_integrations(hass, ["does_not_exist"])
    )
    # Task two should be waiting for the futures created in task one
    task3 = hass.async_create_task(
        loader.async_get_integrations(hass, ["does_not_exist2", "does_not_exist"])
    )
    # Task three should be waiting for the futures created in task one
    integrations_1 = await task1
    assert isinstance(integrations_1["does_not_exist"], loader.IntegrationNotFound)
    assert isinstance(integrations_1["does_not_exist2"], loader.IntegrationNotFound)
    integrations_2 = await task2
    assert isinstance(integrations_2["does_not_exist"], loader.IntegrationNotFound)
    integrations_3 = await task3
    assert isinstance(integrations_3["does_not_exist2"], loader.IntegrationNotFound)
    assert isinstance(integrations_3["does_not_exist"], loader.IntegrationNotFound)

    # Make sure IntegrationNotFound is not cached
    # so configuration errors can be fixed as to
    # not prevent Home Assistant from being restarted
    integration = loader.Integration(
        hass,
        "custom_components.does_not_exist",
        None,
        {
            "name": "Does not exist",
            "domain": "does_not_exist",
        },
    )
    with patch.object(
        loader,
        "_resolve_integrations_from_root",
        return_value={"does_not_exist": integration},
    ):
        integrations = await loader.async_get_integrations(hass, ["does_not_exist"])
    assert integrations["does_not_exist"] is integration