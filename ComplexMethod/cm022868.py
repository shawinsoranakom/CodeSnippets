async def test_services(
    hass: HomeAssistant,
    client: MagicMock,
    storage: MagicMock,
    get_rtm_id_return_value: Any,
    service: str,
    service_data: dict[str, Any],
    get_rtm_id_call_count: int,
    get_rtm_id_call_args: tuple[tuple, dict] | None,
    timelines_call_count: int,
    api_method: str,
    api_method_call_count: int,
    api_method_call_args: tuple[tuple, dict],
    storage_method: str,
    storage_method_call_count: int,
    storage_method_call_args: tuple[tuple, dict] | None,
) -> None:
    """Test create and complete task service."""
    storage.get_rtm_id.return_value = get_rtm_id_return_value
    assert await async_setup_component(hass, DOMAIN, {DOMAIN: CONFIG})

    await hass.services.async_call(DOMAIN, service, service_data, blocking=True)

    assert storage.get_rtm_id.call_count == get_rtm_id_call_count
    assert storage.get_rtm_id.call_args == get_rtm_id_call_args
    assert client.rtm.timelines.create.call_count == timelines_call_count
    client_method = client
    for name in api_method.split("."):
        client_method = getattr(client_method, name)
    assert client_method.call_count == api_method_call_count
    assert client_method.call_args == api_method_call_args
    storage_method_attribute = getattr(storage, storage_method)
    assert storage_method_attribute.call_count == storage_method_call_count
    assert storage_method_attribute.call_args == storage_method_call_args